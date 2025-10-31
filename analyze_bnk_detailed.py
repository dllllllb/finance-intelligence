"""
BNK 파일 상세 분석 - 로직 및 공식 추출
"""
import pandas as pd
import numpy as np

def analyze_sheet_detailed(filepath, sheet_name):
    """특정 시트 상세 분석"""
    print(f"\n{'='*80}")
    print(f"📋 시트: '{sheet_name}' 상세 분석")
    print(f"{'='*80}\n")

    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl', header=None)

        print(f"📏 크기: {df.shape[0]}행 × {df.shape[1]}열\n")

        # 모든 데이터 출력 (처음 50행)
        print("📝 전체 데이터 (처음 50행):")
        print("-" * 80)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        print(df.head(50).to_string())
        print()

        # 숫자 데이터만 추출
        print("\n🔢 숫자 데이터 발견:")
        print("-" * 80)
        for col in df.columns:
            numeric_data = pd.to_numeric(df[col], errors='coerce')
            non_null = numeric_data.dropna()
            if len(non_null) > 0:
                print(f"컬럼 {col}: {len(non_null)}개 숫자 값")
                print(f"  범위: {non_null.min():.2f} ~ {non_null.max():.2f}")
                if len(non_null) <= 20:
                    print(f"  값들: {non_null.values[:10].tolist()}")
                print()

        # 키워드 검색
        print("\n🔍 주요 키워드 검색:")
        print("-" * 80)
        keywords = ['월', '대여료', '금액', '가격', '리스', '할부', '보증', '선납',
                   '잔가', '계산', '수수료', '이자', '기간', '주행']

        for keyword in keywords:
            found = []
            for row_idx in range(min(100, len(df))):
                for col_idx in range(len(df.columns)):
                    cell_value = str(df.iloc[row_idx, col_idx])
                    if keyword in cell_value and cell_value != 'nan':
                        found.append((row_idx, col_idx, cell_value[:100]))

            if found:
                print(f"\n'{keyword}' 발견: {len(found)}건")
                for row, col, val in found[:5]:  # 처음 5개만
                    print(f"  [{row}, {col}]: {val}")

    except Exception as e:
        print(f"❌ 오류: {e}")

def main():
    filepath = "BNK-25-10-V4.xlsm"

    # 주요 시트들 분석
    important_sheets = ['할부기준', 'RVs', 'Cond', 'CDB']

    for sheet_name in important_sheets:
        try:
            analyze_sheet_detailed(filepath, sheet_name)
        except Exception as e:
            print(f"❌ 시트 '{sheet_name}' 분석 실패: {e}")

    print("\n" + "="*80)
    print("✅ 상세 분석 완료")
    print("="*80)

if __name__ == "__main__":
    main()
