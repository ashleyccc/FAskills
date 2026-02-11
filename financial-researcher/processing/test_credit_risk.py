import unittest
from processing.credit_metrics import (
    calculate_icr,
    calculate_leverage,
    calculate_refinancing_risk,
    run_recession_stress_test
)

class TestCreditMetrics(unittest.TestCase):
    def test_icr(self):
        # Healthy
        res = calculate_icr(ebit=100, interest_expense=20)
        self.assertEqual(res.value, 5.0)
        self.assertIn("Strong", res.interpretation)
        
        # Distress
        res = calculate_icr(ebit=80, interest_expense=100)
        self.assertEqual(res.value, 0.8)
        self.assertIn("DISTRESS", res.interpretation)

    def test_leverage(self):
        # High Leverage
        res = calculate_leverage(net_debt=500, ebitda=100)
        self.assertEqual(res.value, 5.0)
        self.assertIn("Speculative", res.interpretation)
        
        # Low Leverage
        res = calculate_leverage(net_debt=100, ebitda=100)
        self.assertEqual(res.value, 1.0)
        self.assertIn("Low", res.interpretation)

    def test_refi_risk(self):
        # Risk: Debt > Liquidity
        res = calculate_refinancing_risk(
            short_term_debt=200, 
            cash_and_equivalents=50, 
            operating_cash_flow=50
        )
        self.assertEqual(res.value, 2.0) # 200 / 100
        self.assertIn("High Refinancing Risk", res.interpretation)

    def test_stress_test(self):
        # Base: EBIT 100, Interest 50 -> ICR 2.0
        # Stress: Rev -15% -> EBIT -30% -> EBIT 70
        # Stress: Rates + -> Interest * 1.25 -> Interest 62.5
        # Stressed ICR = 70 / 62.5 = 1.12
        
        res = run_recession_stress_test(ebit=100, interest_expense=50, revenue=1000)
        self.assertEqual(res.stressed_icr, 1.12)
        self.assertTrue(res.survives)
        
        # Fail case
        # Base: EBIT 100, Interest 80 -> ICR 1.25
        # Stress: EBIT 70
        # Stress: Interest 100
        # Stressed ICR = 0.7
        res = run_recession_stress_test(ebit=100, interest_expense=80, revenue=1000)
        self.assertEqual(res.stressed_icr, 0.7)
        self.assertFalse(res.survives)

if __name__ == '__main__':
    unittest.main()
