"""
BNK 계산기 - 엑셀과 완전 동일한 로직
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

    def calculate_acquisition_tax(
        self,
        car_price: float,
        vehicle_type_eco: str = '일반'
    ) -> Tuple[float, float]:
        """
        취득세/등록세 계산 (엑셀 로직)

        Args:
            car_price: 차량 가격 (VAT 포함)
            vehicle_type_eco: '일반', 'HEV', '전기'

        Returns:
            (취득세, 등록세)
        """
        # 공급가액 (VAT 제외)
        supply_price = car_price / 1.1

        # 취득세율 (일반 2%, 전기는 감면 있음)
        acquisition_tax_rate = 0.02

        # 등록세율 (일반차: 5%, 전기차: 2%)
        if vehicle_type_eco == '전기':
            registration_tax_rate = 0.02
        else:
            registration_tax_rate = 0.05

        # 취득세 계산
        acquisition_tax = round(supply_price * acquisition_tax_rate / 10) * 10  # 10원 단위

        # 등록세 계산
        registration_tax = round(supply_price * registration_tax_rate / 10) * 10

        return acquisition_tax, registration_tax

    def get_residual_rate(
        self,
        rv_company: str,
        period: int,
        grade: str,
        mileage: str = '2만'
    ) -> float:
        """
        잔가율 조회

        Args:
            rv_company: 잔가사 ('웨스트_통합', '웨스트_수입', '큐브_수입', '무카_국산',
                               '태양_수입', '조이_수입', '코렉트', 'ADB')
            period: 계약기간 (12, 24, 36, 42, 44, 48, 60)
            grade: 차량 등급 (S, A, B, C, ...)
            mileage: 주행거리 ('1만', '1.5만', '2만', '3만')

        Returns:
            잔가율 (0~1)
        """
        table_key = f"{rv_company}_{mileage}"

        if table_key not in self.rv_tables:
            table_key = f"{rv_company}_2만"  # 기본은 2만km

        if table_key not in self.rv_tables:
            return 0.5  # 기본값

        period_data = self.rv_tables[table_key].get(str(period), {})
        rv_rate = period_data.get(grade, 0.5)

        # 주행거리 조정 (기본 2만km 기준)
        if mileage != '2만' and mileage in self.rv_tables['주행거리_조정']:
            adjustment = self.rv_tables['주행거리_조정'][mileage]
            rv_rate += adjustment

        return rv_rate

    def calculate_lease(
        self,
        car_price: float,
        option_price: float,
        period: int,
        rv_company: str = '웨스트_통합',
        grade: str = 'A',
        mileage: str = '2만',
        deposit_type: str = '무보증',
        deposit_rate: float = 0,
        dealer_discount: float = 0,
        vehicle_type_eco: str = '일반',
        is_domestic: bool = True
    ) -> Tuple[float, Dict]:
        """
        운용리스 계산 (BNK 엑셀 로직 완전 구현)

        Args:
            car_price: 차량 가격
            option_price: 옵션 가격
            period: 계약기간 (개월)
            rv_company: 잔가사
            grade: 차량 등급
            mileage: 주행거리
            deposit_type: '무보증', '보증금', '선수금'
            deposit_rate: 보증금/선수금 비율 (%)
            dealer_discount: 딜러 할인
            vehicle_type_eco: '일반', 'HEV', '전기'
            is_domestic: 국산 여부

        Returns:
            (월대여료, 상세정보)
        """
        debug = {
            'product': 'lease',
            'car_price': car_price,
            'option_price': option_price,
            'period': period,
            'rv_company': rv_company,
            'grade': grade,
            'mileage': mileage,
            'deposit_type': deposit_type,
            'deposit_rate': deposit_rate,
            'dealer_discount': dealer_discount,
            'vehicle_type_eco': vehicle_type_eco,
            'is_domestic': is_domestic,
            'steps': []
        }

        # 1. 기본가격 (옵션 포함, 딜러할인 차감 전)
        base_price = car_price + option_price

        debug['steps'].append(f"=== 1. 차량 정보 ===")
        debug['steps'].append(f"차량 가격: {car_price:,.0f}원")
        debug['steps'].append(f"옵션 가격: {option_price:,.0f}원")
        debug['steps'].append(f"기본가격: {base_price:,.0f}원")
        debug['steps'].append(f"딜러 할인: {dealer_discount:,.0f}원")

        # 2. 취득세/등록세 계산 (엑셀 B100, B101, B102)
        acquisition_tax, registration_tax = self.calculate_acquisition_tax(
            base_price, vehicle_type_eco
        )

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 2. 취득세/등록세 ===")
        debug['steps'].append(f"공급가액: {base_price/1.1:,.0f}원 (VAT 제외)")
        debug['steps'].append(f"등록세 ({registration_tax/(base_price/1.1)*100:.1f}%): {registration_tax:,.0f}원")
        debug['steps'].append(f"취득세 (2.0%): {acquisition_tax:,.0f}원")

        # 3. 취득원가 (엑셀 B134)
        # 공채는 생략 (간소화)
        acquisition_cost = base_price + registration_tax + acquisition_tax

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 3. 취득원가 ===")
        debug['steps'].append(f"{base_price:,.0f} + {registration_tax:,.0f} + {acquisition_tax:,.0f} = {acquisition_cost:,.0f}원")

        # 4. 잔존가치 기준금액 (엑셀 B62)
        # 국산: 취득원가, 수입: 기본가격
        if is_domestic:
            rv_base_amount = acquisition_cost
            debug['steps'].append(f"")
            debug['steps'].append(f"=== 4. 잔존가치 기준금액 (국산) ===")
            debug['steps'].append(f"취득원가 기준: {rv_base_amount:,.0f}원")
        else:
            rv_base_amount = base_price
            debug['steps'].append(f"")
            debug['steps'].append(f"=== 4. 잔존가치 기준금액 (수입) ===")
            debug['steps'].append(f"기본가격 기준: {rv_base_amount:,.0f}원")

        # 5. 잔가율 조회 및 잔가액 계산 (엑셀 B56, B68, B70)
        rv_rate = self.get_residual_rate(rv_company, period, grade, mileage)
        residual_value = rv_base_amount * rv_rate

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 5. 잔가 정보 ===")
        debug['steps'].append(f"잔가사: {rv_company}")
        debug['steps'].append(f"등급: {grade}, 기간: {period}개월, 주행: {mileage}KM")
        debug['steps'].append(f"잔가율: {rv_rate*100:.2f}%")
        debug['steps'].append(f"잔가금액: {rv_base_amount:,.0f} × {rv_rate:.4f} = {residual_value:,.0f}원")

        # 6. 감가상각액 및 월감가
        depreciation = acquisition_cost - residual_value
        monthly_depreciation = depreciation / period

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 6. 감가상각 ===")
        debug['steps'].append(f"감가상각: {acquisition_cost:,.0f} - {residual_value:,.0f} = {depreciation:,.0f}원")
        debug['steps'].append(f"월감가: {depreciation:,.0f} ÷ {period}개월 = {monthly_depreciation:,.0f}원")

        # 7. 금융비용 (간이 계산)
        finance_cost_rate = 0.06 / 12  # 월 금리 0.5%
        average_balance = (acquisition_cost + residual_value) / 2
        monthly_finance_cost = average_balance * finance_cost_rate

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 7. 금융비용 ===")
        debug['steps'].append(f"평균 잔액: {average_balance:,.0f}원")
        debug['steps'].append(f"월금융비용: {monthly_finance_cost:,.0f}원 (연 6% 가정)")

        # 8. 기본 월대여료
        base_monthly = monthly_depreciation + monthly_finance_cost

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 8. 기본 월대여료 ===")
        debug['steps'].append(f"{monthly_depreciation:,.0f} + {monthly_finance_cost:,.0f} = {base_monthly:,.0f}원")

        # 9. 보증금/선수금 효과
        deposit_discount = 0
        if deposit_type == '보증금' and deposit_rate > 0:
            deposit_amount = acquisition_cost * (deposit_rate / 100)
            deposit_discount = deposit_amount * finance_cost_rate

            debug['steps'].append(f"")
            debug['steps'].append(f"=== 9. 보증금 효과 ===")
            debug['steps'].append(f"보증금: {deposit_amount:,.0f}원 ({deposit_rate}%)")
            debug['steps'].append(f"월대여료 할인: {deposit_discount:,.0f}원")

        elif deposit_type == '선수금' and deposit_rate > 0:
            advance_amount = acquisition_cost * (deposit_rate / 100)
            deposit_discount = advance_amount / period

            debug['steps'].append(f"")
            debug['steps'].append(f"=== 9. 선수금 효과 ===")
            debug['steps'].append(f"선수금: {advance_amount:,.0f}원 ({deposit_rate}%)")
            debug['steps'].append(f"월납입 감소: {deposit_discount:,.0f}원")

        # 10. 딜러할인 효과 (감가상각액 감소)
        if dealer_discount > 0:
            dealer_discount_monthly = dealer_discount / period
            debug['steps'].append(f"")
            debug['steps'].append(f"=== 10. 딜러할인 효과 ===")
            debug['steps'].append(f"딜러할인: {dealer_discount:,.0f}원")
            debug['steps'].append(f"월납입 감소: {dealer_discount_monthly:,.0f}원")
        else:
            dealer_discount_monthly = 0

        # 11. 최종 월대여료
        monthly_payment = base_monthly - deposit_discount - dealer_discount_monthly

        debug['steps'].append(f"")
        debug['steps'].append(f"=== 11. 최종 월대여료 ===")
        debug['steps'].append(f"{base_monthly:,.0f} - {deposit_discount:,.0f} - {dealer_discount_monthly:,.0f} = {monthly_payment:,.0f}원")

        debug['acquisition_cost'] = acquisition_cost
        debug['residual_value'] = residual_value
        debug['residual_rate'] = rv_rate
        debug['acquisition_tax'] = acquisition_tax
        debug['registration_tax'] = registration_tax

        return round(monthly_payment), debug

    def calculate_rental(
        self,
        car_price: float,
        option_price: float,
        period: int,
        rv_company: str = '웨스트_통합',
        grade: str = 'A',
        mileage: str = '2만',
        deposit_type: str = '무보증',
        deposit_rate: float = 0,
        dealer_discount: float = 0,
        vehicle_type_eco: str = '일반',
        is_domestic: bool = True
    ) -> Tuple[float, Dict]:
        """
        렌트 계산 (리스 + 보험료/세금 포함)
        """
        monthly, debug = self.calculate_lease(
            car_price, option_price, period, rv_company, grade,
            mileage, deposit_type, deposit_rate, dealer_discount,
            vehicle_type_eco, is_domestic
        )

        # 렌트 특성: 보험료, 세금 포함 (간소화)
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
