"""
계산 로직 모듈 (모델 기반)
- 추출된 모델 파라미터를 사용하여 월납입금 계산
- Excel 데이터 조회 없이 순수 계산
"""

import json
import os
from typing import Dict, List, Tuple, Optional
import streamlit as st


class ModelBasedCalculator:
    """모델 기반 금융 계산기"""

    # 프로토타입 고정값
    OPTION_PRICE = 0  # 옵션금액
    DEALER_DISCOUNT = 0  # 딜러할인금액
    DEALER_FEE_RATE = 0.01  # 딜러Fee (1%)

    def __init__(self):
        """모델 파라미터 로드"""
        self.params = self._load_params()

    @st.cache_data
    def _load_params(_self) -> Dict:
        """model_params.json 로드 (캐싱)"""
        params_path = os.path.join(os.path.dirname(__file__), "model_params.json")
        with open(params_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_available_companies(self, product_type: str) -> List[str]:
        """이용 가능한 금융사 목록"""
        if product_type not in self.params:
            return []
        return list(self.params[product_type].keys())

    def get_company_params(self, product_type: str, company: str, period: int, mileage: str) -> Optional[Dict]:
        """
        특정 조건의 금융사 파라미터 조회

        Args:
            product_type: 'lease' 또는 'rent'
            company: 금융사명
            period: 계약기간
            mileage: 주행거리

        Returns:
            금융사 파라미터 또는 None
        """
        if product_type not in self.params:
            return None

        if company not in self.params[product_type]:
            return None

        condition_key = f"{period}_{mileage}"
        company_data = self.params[product_type][company]

        if condition_key in company_data:
            return company_data[condition_key]

        # 정확한 조건이 없으면 가장 가까운 조건 찾기
        available_keys = list(company_data.keys())
        if not available_keys:
            return None

        # 같은 기간의 다른 주행거리 찾기
        for key in available_keys:
            if key.startswith(f"{period}_"):
                return company_data[key]

        # 그것도 없으면 첫 번째 것 반환
        return company_data[available_keys[0]]

    def calculate_monthly_payment(
        self,
        car_price: float,
        product_type: str,
        company: str,
        period: int,
        mileage: str,
        deposit_rate: float = 0,
        payment_type: str = '무보증'
    ) -> Tuple[float, Dict]:
        """
        월납입금 계산 (모델 기반)

        Args:
            car_price: 차량 가격
            product_type: 'lease' 또는 'rent'
            company: 금융사명
            period: 계약기간 (개월)
            mileage: 주행거리
            deposit_rate: 보증금/선납금 비율 (0, 10, 20, 30)
            payment_type: '무보증', '보증금', '선수금'

        Returns:
            (월납입금, 디버깅_정보)
        """
        # 파라미터 조회
        params = self.get_company_params(product_type, company, period, mileage)

        if not params:
            return 0, {'error': f'파라미터를 찾을 수 없습니다: {company}, {period}개월, {mileage}'}

        debug = {
            'product': product_type,
            'company': company,
            'period': period,
            'mileage': mileage,
            'payment_type': payment_type,
            'car_price': car_price,
            'option_price': self.OPTION_PRICE,
            'dealer_discount': self.DEALER_DISCOUNT,
            'dealer_fee_rate': self.DEALER_FEE_RATE,
            'deposit_rate': deposit_rate,
            'params': params,
            'steps': []
        }

        # 기본 계산 로직
        base_rate = params['base_rate']
        option_coeff = params['option_coefficient']
        residual_rate = params['residual_rate']

        # 1. 기본 월대여료 (차량가 × 기본요율)
        base_monthly = car_price * base_rate / 100
        debug['steps'].append(f"기본 월대여료: {car_price:,.0f} × {base_rate:.4f}% = {base_monthly:,.0f}원")

        # 2. 옵션 추가 (현재는 0원)
        option_addition = option_coeff * (self.OPTION_PRICE - self.DEALER_DISCOUNT)
        debug['steps'].append(f"옵션 추가: {option_coeff:.6f} × ({self.OPTION_PRICE} - {self.DEALER_DISCOUNT}) = {option_addition:,.2f}원")

        # 3. 보증금/선납금 할인
        deposit_discount = 0
        if payment_type == '보증금' and deposit_rate > 0:
            # 보증금: 월대여료 할인
            # 보증금 30% 기준 6~8% 할인 추정
            discount_rate = deposit_rate / 30 * 0.07  # 30% 기준 7% 할인
            deposit_discount = base_monthly * discount_rate
            debug['steps'].append(f"보증금 할인 ({deposit_rate}%): {base_monthly:,.0f} × {discount_rate:.4f} = -{deposit_discount:,.2f}원")

        elif payment_type == '선수금' and deposit_rate > 0:
            # 선납금: 선납 비율만큼 월대여료 할인
            # 선납 30% 기준 월대여료 15~20% 할인 추정
            discount_rate = deposit_rate / 30 * 0.18  # 30% 기준 18% 할인
            deposit_discount = base_monthly * discount_rate
            debug['steps'].append(f"선납금 할인 ({deposit_rate}%): {base_monthly:,.0f} × {discount_rate:.4f} = -{deposit_discount:,.2f}원")

        # 4. 딜러 Fee 추가
        dealer_fee = car_price * self.DEALER_FEE_RATE * 0.05  # 월납입금에 미세하게 영향
        debug['steps'].append(f"딜러 Fee: {car_price:,.0f} × {self.DEALER_FEE_RATE} × 0.05 = {dealer_fee:,.2f}원")

        # 최종 월납입금
        monthly_payment = base_monthly + option_addition - deposit_discount + dealer_fee
        debug['steps'].append(f"\n최종 월납입금: {base_monthly:,.0f} + {option_addition:,.2f} - {deposit_discount:,.2f} + {dealer_fee:,.2f} = {monthly_payment:,.0f}원")

        return round(monthly_payment), debug

    def calculate_all_companies(
        self,
        car_price: float,
        product_type: str,
        period: int,
        mileage: str,
        deposit_rate: float = 0,
        payment_type: str = '무보증'
    ) -> List[Dict]:
        """
        모든 금융사의 월납입금 계산

        Args:
            car_price: 차량 가격
            product_type: 'lease' 또는 'rent'
            period: 계약기간
            mileage: 주행거리
            deposit_rate: 보증금/선납금 비율
            payment_type: '무보증', '보증금', '선수금'

        Returns:
            계산 결과 리스트 (월납입금 순 정렬)
        """
        companies = self.get_available_companies(product_type)
        results = []

        for company in companies:
            monthly, debug_info = self.calculate_monthly_payment(
                car_price=car_price,
                product_type=product_type,
                company=company,
                period=period,
                mileage=mileage,
                deposit_rate=deposit_rate,
                payment_type=payment_type
            )

            if monthly > 0:
                results.append({
                    'company': company,
                    'payment_type': payment_type,
                    'monthly_payment': monthly,
                    'debug': debug_info
                })

        # 월납입금 순 정렬
        results.sort(key=lambda x: x['monthly_payment'])

        return results


# 전역 인스턴스
_calculator = None

def get_calculator() -> ModelBasedCalculator:
    """계산기 싱글톤 인스턴스 반환"""
    global _calculator
    if _calculator is None:
        _calculator = ModelBasedCalculator()
    return _calculator
