"""ML-powered verdict predictor with SHAP explainability."""

import json
import pickle
from pathlib import Path
from typing import Any
from loguru import logger

import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

from llm.groq_client import GroqClient
from llm.prompt_templates import SYSTEM_LEGAL_ANALYST

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "data" / "processed" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_NAMES = [
    "evidence_count",
    "evidence_strength_avg",
    "witness_count",
    "witness_credibility_avg",
    "precedent_match_score",
    "charge_severity",
    "defense_argument_score",
    "prosecution_argument_score",
    "ipc_section_severity",
    "case_duration_days",
    "judge_type_encoded",
    "bail_status",
    "confession_present",
    "documentary_evidence",
    "forensic_evidence",
]

FEATURE_DISPLAY = {
    "evidence_count": "Number of Evidence Items",
    "evidence_strength_avg": "Average Evidence Strength",
    "witness_count": "Number of Witnesses",
    "witness_credibility_avg": "Witness Credibility",
    "precedent_match_score": "Precedent Support",
    "charge_severity": "Severity of Charges",
    "defense_argument_score": "Defense Argument Quality",
    "prosecution_argument_score": "Prosecution Argument Quality",
    "ipc_section_severity": "IPC Section Severity",
    "case_duration_days": "Case Duration",
    "judge_type_encoded": "Court Level",
    "bail_status": "Bail Status",
    "confession_present": "Confession Present",
    "documentary_evidence": "Documentary Evidence",
    "forensic_evidence": "Forensic Evidence",
}


class VerdictPredictor:
    """ML ensemble for verdict prediction with explainability."""

    def __init__(self):
        self._rf: RandomForestClassifier | None = None
        self._lr: LogisticRegression | None = None
        self._xgb = None
        self._scaler: StandardScaler | None = None
        self._groq = GroqClient()
        self._models_trained = False

        if SKLEARN_AVAILABLE:
            self._try_load_models()

    def generate_training_data(self) -> pd.DataFrame:
        """Generate 1000 synthetic labeled Indian court cases."""
        np.random.seed(42)
        n = 1000
        rng = np.random.default_rng(42)

        evidence_count = rng.integers(1, 20, n)
        evidence_strength_avg = rng.uniform(2, 9, n)
        witness_count = rng.integers(0, 8, n)
        witness_credibility_avg = rng.uniform(3, 9, n)
        precedent_match_score = rng.uniform(0.1, 1.0, n)
        charge_severity = rng.integers(1, 6, n)
        defense_argument_score = rng.uniform(3, 9, n)
        prosecution_argument_score = rng.uniform(3, 9, n)
        ipc_section_severity = rng.integers(1, 6, n)
        case_duration_days = rng.integers(90, 2000, n)
        judge_type_encoded = rng.integers(0, 3, n)
        bail_status = rng.integers(0, 2, n)
        confession_present = rng.integers(0, 2, n)
        documentary_evidence = rng.integers(0, 2, n)
        forensic_evidence = rng.integers(0, 2, n)

        # Conviction probability — realistic Indian court statistics (~60% conviction)
        conviction_prob = (
            0.05 * evidence_count / 20
            + 0.15 * evidence_strength_avg / 10
            + 0.08 * witness_count / 8
            + 0.10 * witness_credibility_avg / 10
            + 0.08 * precedent_match_score
            + 0.08 * charge_severity / 5
            + 0.10 * prosecution_argument_score / 10
            - 0.08 * defense_argument_score / 10
            + 0.08 * ipc_section_severity / 5
            + 0.12 * confession_present
            + 0.10 * forensic_evidence
            + 0.06 * documentary_evidence
        )

        conviction_prob = conviction_prob / conviction_prob.max()
        conviction_prob = 0.35 + 0.45 * conviction_prob  # Scale to 35-80% range
        conviction_prob = np.clip(conviction_prob, 0.05, 0.95)

        noise = rng.normal(0, 0.05, n)
        conviction_prob = np.clip(conviction_prob + noise, 0.05, 0.95)

        conviction = (rng.uniform(0, 1, n) < conviction_prob).astype(int)

        df = pd.DataFrame({
            "evidence_count": evidence_count,
            "evidence_strength_avg": evidence_strength_avg,
            "witness_count": witness_count,
            "witness_credibility_avg": witness_credibility_avg,
            "precedent_match_score": precedent_match_score,
            "charge_severity": charge_severity.astype(float),
            "defense_argument_score": defense_argument_score,
            "prosecution_argument_score": prosecution_argument_score,
            "ipc_section_severity": ipc_section_severity.astype(float),
            "case_duration_days": case_duration_days.astype(float),
            "judge_type_encoded": judge_type_encoded.astype(float),
            "bail_status": bail_status.astype(float),
            "confession_present": confession_present.astype(float),
            "documentary_evidence": documentary_evidence.astype(float),
            "forensic_evidence": forensic_evidence.astype(float),
            "conviction": conviction,
        })

        conviction_rate = conviction.mean()
        logger.info(f"Training data generated: {n} cases, {conviction_rate:.1%} conviction rate")
        return df

    def train_model(self, df: pd.DataFrame | None = None) -> dict:
        """Train Random Forest + Logistic Regression + XGBoost ensemble."""
        if not SKLEARN_AVAILABLE:
            return {"error": "scikit-learn not installed"}

        if df is None:
            df = self.generate_training_data()

        X = df[FEATURE_NAMES].values
        y = df["conviction"].values

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self._scaler = StandardScaler()
        X_train_scaled = self._scaler.fit_transform(X_train)
        X_test_scaled = self._scaler.transform(X_test)

        # Random Forest
        self._rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
        self._rf.fit(X_train, y_train)
        rf_acc = accuracy_score(y_test, self._rf.predict(X_test))

        # Logistic Regression
        self._lr = LogisticRegression(max_iter=1000, random_state=42)
        self._lr.fit(X_train_scaled, y_train)
        lr_acc = accuracy_score(y_test, self._lr.predict(X_test_scaled))

        # XGBoost (optional)
        xgb_acc = None
        if XGB_AVAILABLE:
            self._xgb = xgb.XGBClassifier(n_estimators=200, max_depth=6, random_state=42, eval_metric="logloss", verbosity=0)
            self._xgb.fit(X_train, y_train)
            xgb_acc = accuracy_score(y_test, self._xgb.predict(X_test))

        self._models_trained = True
        self._save_models()

        metrics = {
            "random_forest_accuracy": round(rf_acc, 4),
            "logistic_regression_accuracy": round(lr_acc, 4),
            "xgboost_accuracy": round(xgb_acc, 4) if xgb_acc else None,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "conviction_rate": round(y.mean(), 3),
        }
        logger.info(f"Models trained — RF: {rf_acc:.3f}, LR: {lr_acc:.3f}" + (f", XGB: {xgb_acc:.3f}" if xgb_acc else ""))
        return metrics

    def predict_verdict(self, case_features: dict) -> dict:
        """Predict verdict with ensemble vote."""
        if not self._models_trained:
            if not self._try_load_models():
                self.train_model()

        features = self._extract_features(case_features)
        X = np.array([features])

        probs = []

        if self._rf:
            probs.append(self._rf.predict_proba(X)[0][1])

        if self._lr and self._scaler:
            X_scaled = self._scaler.transform(X)
            probs.append(self._lr.predict_proba(X_scaled)[0][1])

        if self._xgb:
            probs.append(self._xgb.predict_proba(X)[0][1])

        if not probs:
            conviction_prob = 0.5
        else:
            conviction_prob = float(np.mean(probs))

        verdict = "Conviction" if conviction_prob >= 0.5 else "Acquittal"
        confidence = abs(conviction_prob - 0.5) * 2

        key_factors = self._identify_key_factors(features, conviction_prob)
        sentence = self._estimate_sentence(case_features, conviction_prob) if verdict == "Conviction" else None

        return {
            "verdict": verdict,
            "conviction_probability": round(conviction_prob, 4),
            "acquittal_probability": round(1 - conviction_prob, 4),
            "confidence": round(confidence, 4),
            "confidence_level": "High" if confidence > 0.6 else "Medium" if confidence > 0.3 else "Low",
            "key_factors": key_factors,
            "sentence_estimate": sentence,
            "bail_recommendation": "Bail likely" if conviction_prob < 0.4 else "Bail contested" if conviction_prob < 0.65 else "Bail difficult",
            "appeal_grounds": self._suggest_appeal_grounds(case_features, verdict),
        }

    def explain_prediction(self, case_features: dict) -> dict:
        """SHAP-style feature importance for the prediction."""
        if not self._models_trained:
            self.train_model()

        features = self._extract_features(case_features)
        X = np.array([features])

        if SHAP_AVAILABLE and self._rf:
            try:
                explainer = shap.TreeExplainer(self._rf)
                shap_vals = explainer.shap_values(X)
                vals = shap_vals[1][0] if isinstance(shap_vals, list) else shap_vals[0]
                explanation = {
                    FEATURE_DISPLAY.get(name, name): round(float(val), 4)
                    for name, val in zip(FEATURE_NAMES, vals)
                }
                return dict(sorted(explanation.items(), key=lambda x: abs(x[1]), reverse=True))
            except Exception as e:
                logger.warning(f"SHAP failed: {e}")

        # Fallback: use RF feature importances
        if self._rf:
            importances = self._rf.feature_importances_
            weights = {
                FEATURE_DISPLAY.get(name, name): round(float(imp * (f - 0.5) * 2), 4)
                for name, imp, f in zip(FEATURE_NAMES, importances, features)
            }
            return dict(sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True))

        return {}

    def sensitivity_analysis(self, case_features: dict) -> dict:
        """Show how verdict changes with different evidence scenarios."""
        base = self.predict_verdict(case_features)
        base_prob = base["conviction_probability"]
        scenarios = {}

        changes = {
            "Add forensic evidence": {"forensic_evidence": 1},
            "Remove forensic evidence": {"forensic_evidence": 0},
            "Add confession": {"confession_present": 1},
            "No confession": {"confession_present": 0},
            "Add 3 more witnesses": {"witness_count": case_features.get("witness_count", 2) + 3},
            "Strong defense argument": {"defense_argument_score": 9.0},
            "Weak defense argument": {"defense_argument_score": 3.0},
            "Add documentary evidence": {"documentary_evidence": 1},
            "Challenge evidence chain": {"evidence_strength_avg": max(1, case_features.get("evidence_strength_avg", 5) - 2)},
        }

        for scenario_name, override in changes.items():
            modified = {**case_features, **override}
            result = self.predict_verdict(modified)
            delta = result["conviction_probability"] - base_prob
            scenarios[scenario_name] = {
                "conviction_probability": result["conviction_probability"],
                "change": round(delta, 4),
                "change_pct": f"{delta*100:+.1f}%",
                "verdict": result["verdict"],
            }

        return {
            "base_probability": base_prob,
            "base_verdict": base["verdict"],
            "scenarios": scenarios,
        }

    # ── Internal helpers ──────────────────────────────────────────────────

    def _extract_features(self, case_features: dict) -> list[float]:
        """Extract feature vector from case feature dict."""
        judge_map = {"magistrate": 0, "sessions": 1, "high_court": 2, "supreme_court": 3}
        return [
            float(case_features.get("evidence_count", 3)),
            float(case_features.get("evidence_strength_avg", 5.0)),
            float(case_features.get("witness_count", 2)),
            float(case_features.get("witness_credibility_avg", 6.0)),
            float(case_features.get("precedent_match_score", 0.5)),
            float(case_features.get("charge_severity", 3)),
            float(case_features.get("defense_argument_score", 6.0)),
            float(case_features.get("prosecution_argument_score", 6.0)),
            float(case_features.get("ipc_section_severity", 3)),
            float(case_features.get("case_duration_days", 365)),
            float(judge_map.get(case_features.get("judge_type", "sessions"), 1)),
            float(int(case_features.get("bail_status", 0))),
            float(int(case_features.get("confession_present", 0))),
            float(int(case_features.get("documentary_evidence", 1))),
            float(int(case_features.get("forensic_evidence", 0))),
        ]

    def _identify_key_factors(self, features: list[float], prob: float) -> list[str]:
        factors = []
        f = dict(zip(FEATURE_NAMES, features))

        if f["forensic_evidence"] == 1:
            factors.append("Forensic evidence present (+conviction)")
        if f["confession_present"] == 1:
            factors.append("Confession on record (+conviction)")
        if f["evidence_strength_avg"] >= 7:
            factors.append(f"Strong evidence (avg {f['evidence_strength_avg']:.1f}/10)")
        if f["evidence_strength_avg"] <= 4:
            factors.append(f"Weak evidence (avg {f['evidence_strength_avg']:.1f}/10, +acquittal)")
        if f["witness_count"] >= 4:
            factors.append(f"Multiple witnesses ({int(f['witness_count'])})")
        if f["defense_argument_score"] >= 8:
            factors.append("Strong defense arguments (+acquittal)")
        if f["prosecution_argument_score"] >= 8:
            factors.append("Strong prosecution case (+conviction)")
        if f["precedent_match_score"] >= 0.7:
            factors.append("Strong precedent support")
        if f["charge_severity"] >= 4:
            factors.append(f"Serious charges (severity {int(f['charge_severity'])}/5)")

        return factors[:6]

    def _estimate_sentence(self, case_features: dict, prob: float) -> dict | None:
        severity = case_features.get("charge_severity", 3)
        ipc_severity = case_features.get("ipc_section_severity", 3)
        max_severity = max(severity, ipc_severity)

        sentence_map = {
            1: {"min_years": 0.5, "max_years": 3, "likely": "6 months to 2 years"},
            2: {"min_years": 1, "max_years": 5, "likely": "2 to 4 years"},
            3: {"min_years": 3, "max_years": 7, "likely": "4 to 6 years"},
            4: {"min_years": 7, "max_years": 14, "likely": "7 to 10 years"},
            5: {"min_years": 10, "max_years": None, "likely": "Life imprisonment"},
        }
        s = sentence_map.get(max_severity, sentence_map[3])
        s["fine_likely"] = True
        return s

    def _suggest_appeal_grounds(self, case_features: dict, verdict: str) -> list[str]:
        grounds = []
        if verdict == "Conviction":
            if case_features.get("evidence_strength_avg", 5) < 5:
                grounds.append("Insufficiency of evidence — conviction against weight of evidence")
            if not case_features.get("forensic_evidence"):
                grounds.append("Absence of forensic evidence — conviction based on circumstantial evidence only")
            grounds.append("Question of law regarding appreciation of evidence")
            grounds.append("Procedural irregularity — Section 313 statement not properly recorded")
        else:
            grounds.append("Appeal against acquittal on grounds of perverse finding")
            if case_features.get("confession_present"):
                grounds.append("Confession not properly considered by trial court")
        return grounds[:4]

    def _save_models(self) -> None:
        try:
            if self._rf:
                with open(MODELS_DIR / "random_forest.pkl", "wb") as f:
                    pickle.dump(self._rf, f)
            if self._lr:
                with open(MODELS_DIR / "logistic_regression.pkl", "wb") as f:
                    pickle.dump(self._lr, f)
            if self._xgb:
                with open(MODELS_DIR / "xgboost.pkl", "wb") as f:
                    pickle.dump(self._xgb, f)
            if self._scaler:
                with open(MODELS_DIR / "scaler.pkl", "wb") as f:
                    pickle.dump(self._scaler, f)
            logger.info("Models saved to disk")
        except Exception as e:
            logger.error(f"Model save failed: {e}")

    def _try_load_models(self) -> bool:
        try:
            with open(MODELS_DIR / "random_forest.pkl", "rb") as f:
                self._rf = pickle.load(f)
            with open(MODELS_DIR / "logistic_regression.pkl", "rb") as f:
                self._lr = pickle.load(f)
            if (MODELS_DIR / "xgboost.pkl").exists():
                with open(MODELS_DIR / "xgboost.pkl", "rb") as f:
                    self._xgb = pickle.load(f)
            with open(MODELS_DIR / "scaler.pkl", "rb") as f:
                self._scaler = pickle.load(f)
            self._models_trained = True
            logger.info("Pre-trained models loaded from disk")
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.warning(f"Model load failed: {e}")
            return False


if __name__ == "__main__":
    predictor = VerdictPredictor()
    metrics = predictor.train_model()
    print("\nTraining Metrics:", json.dumps(metrics, indent=2))

    sample_case = {
        "evidence_count": 8,
        "evidence_strength_avg": 7.2,
        "witness_count": 3,
        "witness_credibility_avg": 7.5,
        "precedent_match_score": 0.75,
        "charge_severity": 4,
        "defense_argument_score": 6.0,
        "prosecution_argument_score": 7.5,
        "ipc_section_severity": 4,
        "case_duration_days": 450,
        "judge_type": "sessions",
        "bail_status": 0,
        "confession_present": 0,
        "documentary_evidence": 1,
        "forensic_evidence": 1,
    }
    result = predictor.predict_verdict(sample_case)
    print("\nVerdict Prediction:", json.dumps(result, indent=2))
