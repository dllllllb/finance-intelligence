"""
Excel 데이터 분석 스크립트
- 금융사별 잔가율, 요율, 계수 추출
"""

import pandas as pd
import numpy as np
import json
import os


def analyze_lease_data(data_dir="../ref"):
    """리스 데이터 분석"""
    filepath = os.path.join(data_dir, "lease.xlsx")
    excel_file = pd.ExcelFile(filepath)

    results = {}

    for sheet_name in excel_file.sheet_names:
        print(f"\n분석 중: {sheet_name}")
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=0)

        # 실제 데이터만 (NaN 행 제거)
        if len(df.columns) == 0:
            print(f"  → 컬럼 없음, 건너뛰기")
            continue

        # 첫 번째 컬럼이 있는 행만
        first_col = df.columns[0]
        df = df[df[first_col].notna()].copy()
        df = df.reset_index(drop=True)

        if len(df) == 0:
            print(f"  → 데이터 없음, 건너뛰기")
            continue

        # 계약기간, 주행거리 파싱
        parts = sheet_name.split('_')
        period = int(parts[0].replace('개월', ''))
        mileage = parts[1]

        key = f"{period}_{mileage}"
        results[key] = {
            'period': period,
            'mileage': mileage,
            'companies': {}
        }

        # 금융사별 분석 (1st만 분석)
        for idx, row in df.iterrows():
            # 차량가격은 엔진cc 컬럼 (4번째)
            try:
                car_price = float(row.iloc[4])
            except:
                continue

            if not car_price or car_price == 0 or pd.isna(car_price):
                continue

            # 1st 금융사 데이터
            try:
                # 1st 컬럼 찾기
                columns = row.index.tolist()
                company_idx = None
                for i, col in enumerate(columns):
                    if '1st' in str(col):
                        company_idx = i
                        break

                if company_idx is None:
                    continue

                company = row.iloc[company_idx]
                if pd.isna(company):
                    continue

                # 무보증 (company_idx 기준 +1, +2, ...)
                monthly_0 = float(row.iloc[company_idx + 1])
                monthly_500 = float(row.iloc[company_idx + 2])
                fee_1 = float(row.iloc[company_idx + 7])

                # 보증금 (company_idx + 12, 13, 14)
                deposit_monthly_0 = float(row.iloc[company_idx + 12])
                deposit_monthly_500 = float(row.iloc[company_idx + 13])
                deposit_ref_0 = float(row.iloc[company_idx + 14])

                # 분석
                # 1. 기본 요율 (차량가 대비 월대여료)
                base_rate = monthly_0 / car_price * 100

                # 2. 옵션 계수 (500만원당 월대여료 증가액)
                option_coefficient = (monthly_500 - monthly_0) / 5000000

                # 3. 잔가율 추정 (월대여료로부터 역산)
                # 월대여료 = (차량가 - 잔가) / 개월수 + 이자 등
                # 간단히: 잔가율 = 1 - (월대여료 * 개월수 / 차량가)
                residual_rate = 1 - (monthly_0 * period / car_price)
                residual_rate = max(0, min(1, residual_rate))  # 0~1 사이

                # 4. 보증금 할인 계수
                # 보증금 30% 기준으로 월대여료가 얼마나 줄어드는지
                deposit_discount_rate = (deposit_ref_0 - deposit_monthly_0) / deposit_ref_0 * 100 if deposit_ref_0 > 0 else 0

                if company not in results[key]['companies']:
                    results[key]['companies'][company] = []

                results[key]['companies'][company].append({
                    'car_price': car_price,
                    'base_rate': base_rate,
                    'option_coefficient': option_coefficient,
                    'residual_rate': residual_rate,
                    'deposit_discount_rate': deposit_discount_rate,
                    'monthly_0': monthly_0,
                    'monthly_500': monthly_500,
                    'fee_1': fee_1
                })

            except Exception as e:
                continue

    return results


def analyze_rent_data(data_dir="../ref"):
    """렌트 데이터 분석"""
    filepath = os.path.join(data_dir, "rent.xlsx")
    excel_file = pd.ExcelFile(filepath)

    results = {}

    for sheet_name in excel_file.sheet_names:
        print(f"\n분석 중: {sheet_name}")
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=0)

        # 실제 데이터만
        if len(df.columns) == 0:
            print(f"  → 컬럼 없음, 건너뛰기")
            continue

        first_col = df.columns[0]
        df = df[df[first_col].notna()].copy()
        df = df.reset_index(drop=True)

        if len(df) == 0:
            print(f"  → 데이터 없음, 건너뛰기")
            continue

        # 계약기간, 주행거리 파싱
        parts = sheet_name.split('_')
        period = int(parts[0].replace('개월', ''))
        mileage = parts[1]

        key = f"{period}_{mileage}"
        results[key] = {
            'period': period,
            'mileage': mileage,
            'companies': {}
        }

        # 금융사별 분석 (1st만)
        for idx, row in df.iterrows():
            try:
                car_price = float(row.iloc[4])  # 5번째 컬럼이 가격
                if not car_price or car_price == 0 or pd.isna(car_price):
                    continue

                # 1st 컬럼 찾기
                columns = row.index.tolist()
                company_idx = None
                for i, col in enumerate(columns):
                    if '1st' in str(col):
                        company_idx = i
                        break

                if company_idx is None:
                    continue

                company = row.iloc[company_idx]
                if pd.isna(company):
                    continue

                # 무보증
                monthly_0 = float(row.iloc[company_idx + 1])
                monthly_500 = float(row.iloc[company_idx + 2])
                fee_1 = float(row.iloc[company_idx + 6])

                # 분석
                base_rate = monthly_0 / car_price * 100
                option_coefficient = (monthly_500 - monthly_0) / 5000000
                residual_rate = 1 - (monthly_0 * period / car_price)
                residual_rate = max(0, min(1, residual_rate))

                if company not in results[key]['companies']:
                    results[key]['companies'][company] = []

                results[key]['companies'][company].append({
                    'car_price': car_price,
                    'base_rate': base_rate,
                    'option_coefficient': option_coefficient,
                    'residual_rate': residual_rate,
                    'monthly_0': monthly_0,
                    'monthly_500': monthly_500,
                    'fee_1': fee_1
                })

            except Exception as e:
                continue

    return results


def aggregate_company_params(analysis_results):
    """금융사별 평균 파라미터 계산"""
    aggregated = {}

    for key, data in analysis_results.items():
        period = data['period']
        mileage = data['mileage']

        for company, samples in data['companies'].items():
            if company not in aggregated:
                aggregated[company] = {}

            condition_key = f"{period}_{mileage}"

            # 평균 계산
            base_rates = [s['base_rate'] for s in samples]
            option_coeffs = [s['option_coefficient'] for s in samples]
            residual_rates = [s['residual_rate'] for s in samples]

            aggregated[company][condition_key] = {
                'period': period,
                'mileage': mileage,
                'base_rate': np.mean(base_rates),
                'base_rate_std': np.std(base_rates),
                'option_coefficient': np.mean(option_coeffs),
                'residual_rate': np.mean(residual_rates),
                'residual_rate_std': np.std(residual_rates),
                'sample_count': len(samples)
            }

    return aggregated


def save_model_params(lease_params, rent_params, output_dir="../src"):
    """모델 파라미터를 JSON으로 저장"""

    model_params = {
        'lease': lease_params,
        'rent': rent_params,
        'metadata': {
            'version': '1.0',
            'description': 'Extracted from lease.xlsx and rent.xlsx',
            'date': '2025-10-29'
        }
    }

    output_path = os.path.join(output_dir, "model_params.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(model_params, f, ensure_ascii=False, indent=2)

    print(f"\n모델 파라미터 저장 완료: {output_path}")
    return output_path


def main():
    print("=" * 60)
    print("금융 데이터 분석 시작")
    print("=" * 60)

    # 리스 데이터 분석
    print("\n[1/4] 리스 데이터 분석 중...")
    lease_analysis = analyze_lease_data()
    lease_params = aggregate_company_params(lease_analysis)
    print(f"✓ 리스 금융사 수: {len(lease_params)}")

    # 렌트 데이터 분석
    print("\n[2/4] 렌트 데이터 분석 중...")
    rent_analysis = analyze_rent_data()
    rent_params = aggregate_company_params(rent_analysis)
    print(f"✓ 렌트 금융사 수: {len(rent_params)}")

    # 파라미터 저장
    print("\n[3/4] 모델 파라미터 저장 중...")
    output_path = save_model_params(lease_params, rent_params)

    # 요약 출력
    print("\n[4/4] 분석 요약")
    print("=" * 60)
    print(f"리스 금융사: {', '.join(list(lease_params.keys())[:5])}...")
    print(f"렌트 금융사: {', '.join(list(rent_params.keys())[:5])}...")

    # 샘플 출력
    if lease_params:
        first_company = list(lease_params.keys())[0]
        first_condition = list(lease_params[first_company].keys())[0]
        print(f"\n샘플 파라미터 ({first_company}, {first_condition}):")
        print(json.dumps(lease_params[first_company][first_condition], indent=2, ensure_ascii=False))

    print("\n분석 완료! ✓")


if __name__ == "__main__":
    main()
