"""
BNK 계산기 - 엑셀과 동일한 로직
"""
import json
import os
from typing import Dict, Tuple, Optional

class BNKCalculator:
    """BNK 엑셀 견적서와 동일한 계산 로직"""

    def __init__(self):
        """BNK 잔가율 테이블 로드"""
        self.rv_tables = self._load_rv_tables()

    def _load_rv_tables(self) -> Dict:
        """잔가율 테이블 로드"""
        rv_path = os.path.join(os.path.dirname(__file__), "bnk_rv_tables.json")
        with open(rv_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_residual_rate(
        self,
        vehicle_type: str,
        period: int,
        grade: str,
        mileage: str = '2만'
    ) -> float:
        """
        잔가율 조회

        Args:
            vehicle_type: '웨스트_통합', '웨스트_수입', '큐브_수입', '무카_국산'
            period: 계약기간 (12, 24, 36, 42, 44, 48, 60)
            grade: 차량 등급 (S, A, B, C, ...)
            mileage: 주행거리 ('1만', '1.5만', '2만', '3만')

        Returns:
            잔가율 (0~1)
        """
        table_key = f"{vehicle_type}_{mileage}"

        if table_key not in self.rv_tables:
            table_key = f"{vehicle_type}_2만"  # 기본은 2만km

        if table_key not in self.rv_tables:
            return 0.5  # 기본값

        period_data = self.rv_tables[table_key].get(str(period), {})
        rv_rate = period_data.get(grade, 0.5)

        # 주행거리 조정
        if mileage in self.rv_tables['주행거리_조정']:
            adjustment = self.rv_tables['주행거리_조정'][mileage]
            rv_rate += adjustment

        return rv_rate

    def calculate_lease(
        self,
        car_price: float,
        option_price: float,
        period: int,
        vehicle_type: str,
        grade: str,
        mileage: str = '2만',
        deposit_type: str = '무보증',
        deposit_rate: float = 0,
        dealer_discount: float = 0
    ) -> Tuple[float, Dict]:
        """
        운용리스 계산 (BNK 엑셀 로직)

        Args:
            car_price: 차량 가격
            option_price: 옵션 가격
            period: 계약기간 (개월)
            vehicle_type: 차량 유형
            grade: 차량 등급
            mileage: 주행거리
            deposit_type: '무보증', '보증금', '선수금'
            deposit_rate: 보증금/선수금 비율 (%)
            dealer_discount: 딜러 할인

        Returns:
            (월대여료, 상세정보)
        """
        debug = {
            'product': 'lease',
            'car_price': car_price,
            'option_price': option_price,
            'period': period,
            'vehicle_type': vehicle_type,
            'grade': grade,
            'mileage': mileage,
            'deposit_type': deposit_type,
            'deposit_rate': deposit_rate,
            'dealer_discount': dealer_discount,
            'steps': []
        }

        # 1. 총 차량가
        total_price = car_price + option_price - dealer_discount
        debug['steps'].append(f"=== 차량 정보 ===")
        debug['steps'].append(f"차량 가격: {car_price:,.0f}원")
        debug['steps'].append(f"옵션 가격: {option_price:,.0f}원")
        debug['steps'].append(f"딜러 할인: {dealer_discount:,.0f}원")
        debug['steps'].append(f"총 차량가: {total_price:,.0f}원")

        # 2. 잔가 계산
        rv_rate = self.get_residual_rate(vehicle_type, period, grade, mileage)
        residual_value = total_price * rv_rate

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 잔가 정보 ===")
        debug['steps'].append(f"잔가율: {rv_rate*100:.2f}%")
        debug['steps'].append(f"잔가금액: {total_price:,.0f} × {rv_rate:.4f} = {residual_value:,.0f}원")

        # 3. 감가상각액
        depreciation = total_price - residual_value
        monthly_depreciation = depreciation / period

        debug['steps'].append(f"감가상각: {total_price:,.0f} - {residual_value:,.0f} = {depreciation:,.0f}원")
        debug['steps'].append(f"월감가: {depreciation:,.0f} ÷ {period}개월 = {monthly_depreciation:,.0f}원")

        # 4. 금융비용 (간이 계산 - 실제 엑셀은 더 복잡)
        # 연 금리 약 6% 가정
        finance_cost_rate = 0.06 / 12  # 월 금리
        average_balance = total_price / 2  # 평균 잔액
        monthly_finance_cost = average_balance * finance_cost_rate

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 금융비용 ===")
        debug['steps'].append(f"월금융비용: {monthly_finance_cost:,.0f}원 (연 6% 가정)")

        # 5. 기본 월대여료
        base_monthly = monthly_depreciation + monthly_finance_cost

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 기본 월대여료 ===")
        debug['steps'].append(f"{monthly_depreciation:,.0f} + {monthly_finance_cost:,.0f} = {base_monthly:,.0f}원")

        # 6. 보증금/선수금 효과
        deposit_discount = 0
        if deposit_type == '보증금' and deposit_rate > 0:
            # 보증금: 월대여료 할인
            deposit_amount = total_price * (deposit_rate / 100)
            deposit_discount = deposit_amount * finance_cost_rate
            debug['steps'].append(f"")
            debug['steps'].append(f"=== 보증금 효과 ===")
            debug['steps'].append(f"보증금: {deposit_amount:,.0f}원 ({deposit_rate}%)")
            debug['steps'].append(f"할인: {deposit_discount:,.0f}원")

        elif deposit_type == '선수금' and deposit_rate > 0:
            # 선수금: 선납 효과
            advance_amount = total_price * (deposit_rate / 100)
            advance_months = period * (deposit_rate / 100)  # 선납 개월 수
            deposit_discount = advance_amount / period

            debug['steps'].append(f"")
            debug['steps'].append(f"=== 선수금 효과 ===")
            debug['steps'].append(f"선수금: {advance_amount:,.0f}원 ({deposit_rate}%)")
            debug['steps'].append(f"월납입 감소: {deposit_discount:,.0f}원")

        # 7. 최종 월대여료
        monthly_payment = base_monthly - deposit_discount

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 최종 월대여료 ===")
        debug['steps'].append(f"{base_monthly:,.0f} - {deposit_discount:,.0f} = {monthly_payment:,.0f}원")

        debug['residual_value'] = residual_value
        debug['residual_rate'] = rv_rate

        return round(monthly_payment), debug

    def calculate_rental(
        self,
        car_price: float,
        option_price: float,
        period: int,
        vehicle_type: str,
        grade: str,
        mileage: str = '2만',
        deposit_type: str = '무보증',
        deposit_rate: float = 0,
        dealer_discount: float = 0
    ) -> Tuple[float, Dict]:
        """
        렌트 계산 (리스와 유사하나 약간 다른 로직)
        """
        # 렌트는 리스와 거의 동일하지만 금리가 약간 다름
        monthly, debug = self.calculate_lease(
            car_price, option_price, period, vehicle_type, grade,
            mileage, deposit_type, deposit_rate, dealer_discount
        )

        # 렌트 특성: 보험료, 세금 포함
        insurance_tax = car_price * 0.005  # 월 0.5%
        debug['steps'].append(f"")
        debug['steps'].append(f"=== 렌트 추가비용 ===")
        debug['steps'].append(f"보험료+세금: {insurance_tax:,.0f}원")

        monthly_rental = monthly + insurance_tax
        debug['steps'].append(f"")
        debug['steps'].append(f"=== 최종 렌트료 ===")
        debug['steps'].append(f"{monthly:,.0f} + {insurance_tax:,.0f} = {monthly_rental:,.0f}원")

        debug['product'] = 'rental'

        return round(monthly_rental), debug


# 싱글톤 인스턴스
_bnk_calculator = None

def get_bnk_calculator() -> BNKCalculator:
    """BNK 계산기 싱글톤 인스턴스"""
    global _bnk_calculator
    if _bnk_calculator is None:
        _bnk_calculator = BNKCalculator()
    return _bnk_calculator
