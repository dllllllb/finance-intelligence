"""
데이터 로더 모듈
- 차량 정보, 리스/렌트 견적 데이터를 로드하고 파싱
"""

import pandas as pd
import os
from typing import Dict, List, Tuple, Optional
import streamlit as st


class DataLoader:
    """금융계산기 데이터 로더"""

    def __init__(self, data_dir: str = "ref"):
        """
        Args:
            data_dir: 데이터 파일이 있는 디렉토리 경로
        """
        self.data_dir = data_dir
        self.carinfo = None
        self.lease_data = {}  # {시트명: DataFrame}
        self.rent_data = {}   # {시트명: DataFrame}

    @st.cache_data
    def load_all_data(_self):
        """모든 데이터 로드 (캐싱)"""
        _self.load_carinfo()
        # lease.xlsx와 rent.xlsx는 model_params.json 추출 후 불필요
        # 계산은 calculator.py의 model_params.json을 사용
        return True

    def load_carinfo(self):
        """차량 정보 로드"""
        filepath = os.path.join(self.data_dir, "carinfo.xlsx")
        self.carinfo = pd.read_excel(filepath)
        # 결측치 처리
        self.carinfo = self.carinfo.fillna("")
        return self.carinfo

    def load_lease_data(self):
        """리스 데이터 로드 (모든 시트)"""
        filepath = os.path.join(self.data_dir, "lease.xlsx")
        excel_file = pd.ExcelFile(filepath)

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet_name, header=0)
            self.lease_data[sheet_name] = df

        return self.lease_data

    def load_rent_data(self):
        """렌트 데이터 로드 (모든 시트)"""
        filepath = os.path.join(self.data_dir, "rent.xlsx")
        excel_file = pd.ExcelFile(filepath)

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet_name, header=0)
            self.rent_data[sheet_name] = df

        return self.rent_data

    def get_brands(self) -> List[str]:
        """브랜드 목록 반환"""
        if self.carinfo is None:
            self.load_carinfo()
        return sorted(self.carinfo['brand'].unique().tolist())

    def get_models(self, brand: str) -> List[str]:
        """특정 브랜드의 모델 목록 반환"""
        if self.carinfo is None:
            self.load_carinfo()
        models = self.carinfo[self.carinfo['brand'] == brand]['model'].unique()
        return sorted(models.tolist())

    def get_grades(self, brand: str, model: str) -> List[Dict]:
        """특정 브랜드/모델의 등급 목록 반환"""
        if self.carinfo is None:
            self.load_carinfo()

        filtered = self.carinfo[
            (self.carinfo['brand'] == brand) &
            (self.carinfo['model'] == model)
        ]

        grades = []
        for _, row in filtered.iterrows():
            grades.append({
                'id_cargrade': row['id_cargrade'],
                'grade': row['grade'],
                'name': row['name'],
                'price': row['price'],
                'fuel_type': row['fuel_type'],
                'engine_size': row['engine_size'],
                'body_style': row['body_style']
            })

        return grades

    def get_car_info(self, id_cargrade: int) -> Optional[Dict]:
        """차량 ID로 차량 정보 조회"""
        if self.carinfo is None:
            self.load_carinfo()

        car = self.carinfo[self.carinfo['id_cargrade'] == id_cargrade]
        if len(car) == 0:
            return None

        row = car.iloc[0]
        return {
            'id_cargrade': row['id_cargrade'],
            'brand': row['brand'],
            'model': row['model'],
            'grade': row['grade'],
            'name': row['name'],
            'price': row['price'],
            'fuel_type': row['fuel_type'],
            'engine_size': row['engine_size'],
            'body_style': row['body_style']
        }

    def parse_sheet_name(self, sheet_name: str) -> Tuple[int, str]:
        """
        시트명 파싱
        예: "36개월_2만km" -> (36, "2만km")
        """
        parts = sheet_name.split('_')
        if len(parts) != 2:
            return None, None

        period = int(parts[0].replace('개월', ''))
        mileage = parts[1]

        return period, mileage

    def get_available_periods(self, product_type: str) -> List[int]:
        """
        이용 가능한 계약기간 목록
        Args:
            product_type: 'lease' 또는 'rent'
        """
        data = self.lease_data if product_type == 'lease' else self.rent_data
        periods = set()

        for sheet_name in data.keys():
            period, _ = self.parse_sheet_name(sheet_name)
            if period:
                periods.add(period)

        return sorted(list(periods))

    def get_available_mileages(self, product_type: str, period: int) -> List[str]:
        """
        특정 계약기간의 이용 가능한 주행거리 목록
        Args:
            product_type: 'lease' 또는 'rent'
            period: 계약기간 (개월)
        """
        data = self.lease_data if product_type == 'lease' else self.rent_data
        mileages = []

        for sheet_name in data.keys():
            p, m = self.parse_sheet_name(sheet_name)
            if p == period:
                mileages.append(m)

        return sorted(mileages)

    def get_finance_data(self, product_type: str, period: int, mileage: str,
                         id_cargrade: int) -> Optional[pd.Series]:
        """
        특정 조건의 금융 데이터 조회
        Args:
            product_type: 'lease' 또는 'rent'
            period: 계약기간
            mileage: 주행거리
            id_cargrade: 차량 ID
        Returns:
            해당 차량의 금융사 데이터 (행 전체)
        """
        sheet_name = f"{period}개월_{mileage}"
        data = self.lease_data if product_type == 'lease' else self.rent_data

        if sheet_name not in data:
            return None

        df = data[sheet_name]

        # 겟차번호로 차량 찾기
        car_data = df[df['겟차번호'] == id_cargrade]

        if len(car_data) == 0:
            return None

        return car_data.iloc[0]

    def parse_finance_companies(self, row: pd.Series, product_type: str) -> List[Dict]:
        """
        금융사 데이터 파싱
        Args:
            row: 차량 데이터 행
            product_type: 'lease' 또는 'rent'
        Returns:
            금융사 데이터 리스트
        """
        companies = []

        # 컬럼 인덱스 찾기 (1st, 2nd, 3rd, ...)
        columns = row.index.tolist()

        # nth 회사 찾기
        nth_indices = []
        for i, col in enumerate(columns):
            if isinstance(col, str) and ('1st' in col or '2nd' in col or '3rd' in col or
                                          '4th' in col or '5th' in col or '6th' in col or
                                          '7th' in col or '8th' in col or '9th' in col or
                                          '10th' in col or '11th' in col or '12th' in col or
                                          '13th' in col or '14th' in col):
                nth_indices.append(i)

        # 각 금융사 블록 파싱
        for nth_idx in nth_indices:
            try:
                company_data = self._parse_company_block(row, nth_idx, columns)
                if company_data:
                    companies.append(company_data)
            except Exception as e:
                # 파싱 실패 시 건너뛰기
                continue

        return companies

    def _parse_company_block(self, row: pd.Series, start_idx: int, columns: List) -> Optional[Dict]:
        """
        개별 금융사 블록 파싱
        """
        # 무보증 데이터
        no_deposit = {}
        company_name_col = columns[start_idx]
        company_name = row[company_name_col]

        if pd.isna(company_name) or company_name == "":
            return None

        # 무보증 회사명
        no_deposit['company'] = company_name
        no_deposit['type'] = '무보증'

        # 무보증 데이터 추출 (start_idx 기준 +1, +2, ...)
        try:
            no_deposit['monthly_0'] = row[columns[start_idx + 1]]  # 무보증월대여료옵션0
            no_deposit['monthly_500'] = row[columns[start_idx + 2]]  # 무보증월대여료옵션500
            no_deposit['dealer_offset'] = row[columns[start_idx + 3]]  # 무보증딜러오프셋
            no_deposit['acquisition_price'] = row[columns[start_idx + 5]]  # 무보증인수가격
            no_deposit['fee_offset'] = row[columns[start_idx + 6]]  # 무보증Fee오프셋
            no_deposit['fee_1'] = row[columns[start_idx + 7]]  # 무보증1fee
        except:
            no_deposit = None

        # 보증금 데이터
        deposit = {}
        try:
            deposit['company'] = row[columns[start_idx + 11]]  # 보증금회사명
            if pd.isna(deposit['company']) or deposit['company'] == "":
                deposit = None
            else:
                deposit['type'] = '보증금'
                deposit['monthly_0'] = row[columns[start_idx + 12]]  # 보증금월대여료옵션0
                deposit['monthly_500'] = row[columns[start_idx + 13]]  # 보증금월대여료옵션500
                deposit['monthly_0_ref'] = row[columns[start_idx + 14]]  # 월대여료옵션0ref
                deposit['monthly_500_ref'] = row[columns[start_idx + 15]]  # 월대여료옵션500ref
                deposit['dealer_offset'] = row[columns[start_idx + 16]]  # 보증금딜러오프셋
                deposit['acquisition_price'] = row[columns[start_idx + 18]]  # 보증금인수가격
                deposit['fee_offset'] = row[columns[start_idx + 19]]  # 보증금Fee오프셋
                deposit['fee_1'] = row[columns[start_idx + 20]]  # 보증금1fee
        except:
            deposit = None

        # 선수금 데이터
        advance = {}
        try:
            advance['company'] = row[columns[start_idx + 24]]  # 선수금회사명
            if pd.isna(advance['company']) or advance['company'] == "":
                advance = None
            else:
                advance['type'] = '선수금'
                advance['monthly_0'] = row[columns[start_idx + 25]]  # 선수금월대여료옵션0
                advance['monthly_500'] = row[columns[start_idx + 26]]  # 선수금월대여료옵션500
                advance['monthly_0_ref'] = row[columns[start_idx + 27]]  # 월대여료옵션0ref
                advance['monthly_500_ref'] = row[columns[start_idx + 28]]  # 월대여료옵션500ref
                advance['dealer_offset'] = row[columns[start_idx + 29]]  # 선수금딜러오프셋
                advance['acquisition_price'] = row[columns[start_idx + 31]]  # 선수금인수가격
                advance['fee_offset'] = row[columns[start_idx + 32]]  # 선수금Fee오프셋
                advance['fee_1'] = row[columns[start_idx + 33]]  # 선수금1fee
        except:
            advance = None

        result = []
        if no_deposit:
            result.append(no_deposit)
        if deposit:
            result.append(deposit)
        if advance:
            result.append(advance)

        return result if result else None


# 전역 인스턴스
_data_loader = None

def get_data_loader(data_dir: str = "ref") -> DataLoader:
    """데이터 로더 싱글톤 인스턴스 반환"""
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader(data_dir)
        _data_loader.load_all_data()
    return _data_loader
