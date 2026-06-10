class ConfidenceEngine:
    @staticmethod
    def calculate(matcher_score: float, planner_score: float, join_score: float) -> float:
        """
        Calculates a unified confidence score (0-1).
        matcher_score: average or max score from semantic matching (0-100 scale, will be normalized)
        planner_score: ML intent confidence (0-1)
        join_score: confidence in the join paths (0-1)
        """
        norm_matcher = min(matcher_score / 100.0, 1.0)
        
        # 0.50 * matcher + 0.30 * planner + 0.20 * join
        confidence = (0.50 * norm_matcher) + (0.30 * planner_score) + (0.20 * join_score)
        return round(min(confidence, 1.0), 4)
