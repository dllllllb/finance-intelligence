"""
Financial Intelligence - 자동차 리스/렌트 월납입금 계산기 (모델 기반)
"""

import streamlit as st
import sys
import os
import json
import pandas as pd

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_loader import get_data_loader
from calculator import get_calculator


# 페이지 설정
st.set_page_config(
    page_title="Financial Intelligence",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .bot-message {
        background-color: #f0f0f0;
    }
    .user-message {
        background-color: #e3f2fd;
        text-align: right;
    }
    .result-card {
        border: 1px solid #ddd;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    .rank-1 { background-color: #fff9c4; }
    .rank-2 { background-color: #f0f4c3; }
    .rank-3 { background-color: #dcedc8; }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """세션 상태 초기화"""
    if 'page' not in st.session_state:
        st.session_state.page = 'calculator'
    if 'step' not in st.session_state:
        st.session_state.step = 'brand'
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'selected_brand' not in st.session_state:
        st.session_state.selected_brand = None
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = None
    if 'selected_car' not in st.session_state:
        st.session_state.selected_car = None
    if 'product_type' not in st.session_state:
        st.session_state.product_type = None
    if 'period' not in st.session_state:
        st.session_state.period = None
    if 'mileage' not in st.session_state:
        st.session_state.mileage = None
    if 'deposit_rate' not in st.session_state:
        st.session_state.deposit_rate = None
    if 'deposit_type' not in st.session_state:
        st.session_state.deposit_type = None
    if 'dealer_discount' not in st.session_state:
        st.session_state.dealer_discount = 0
    if 'dealer_fee_rate' not in st.session_state:
        st.session_state.dealer_fee_rate = 1.0
    if 'option_price' not in st.session_state:
        st.session_state.option_price = 0
    if 'results' not in st.session_state:
        st.session_state.results = None


def render_sidebar():
    """사이드바 메뉴"""
    with st.sidebar:
        st.markdown("## 📌 메뉴")

        if st.button("🧮 계산기", use_container_width=True, type="primary" if st.session_state.page == 'calculator' else "secondary"):
            st.session_state.page = 'calculator'
            st.rerun()

        if st.button("📊 모델 파라미터", use_container_width=True, type="primary" if st.session_state.page == 'params' else "secondary"):
            st.session_state.page = 'params'
            st.rerun()

        st.markdown("---")
        st.markdown("### ℹ️ 정보")
        st.info("""
**버전**: 2.0 (모델 기반)
**방식**: Excel 데이터 학습 후 계산
**데이터**: 리스 16개 조건, 렌트 12개 조건
        """)


def add_chat_message(role: str, message: str):
    """채팅 메시지 추가"""
    st.session_state.chat_history.append({'role': role, 'message': message})


# ================ 계산기 페이지 ================

def render_calculator_page():
    """계산기 페이지"""
    st.markdown('<div class="main-header">🚗 Financial Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">자동차 리스/렌트 월납입금 계산기 (모델 기반)</p>', unsafe_allow_html=True)

    data_loader = get_data_loader(data_dir="ref")

    # 계산 수행
    if st.session_state.step == 'calculate' and st.session_state.results is None:
        calculate_results()

    # 3단 레이아웃
    col1, col2, col3 = st.columns([3, 3.5, 3.5])

    with col1:
        render_chat_ui(data_loader)

    with col2:
        render_summary_ui()

    with col3:
        render_debug_ui()


def render_chat_ui(data_loader):
    """좌측 채팅 UI"""
    st.markdown("### 💬 차량 선택")

    # 채팅 히스토리
    chat_container = st.container()
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat['role'] == 'bot':
                st.markdown(f'<div class="chat-message bot-message">🤖 {chat["message"]}</div>',
                          unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message user-message">👤 {chat["message"]}</div>',
                          unsafe_allow_html=True)

    st.markdown("---")

    # 단계별 입력
    if st.session_state.step == 'brand':
        st.markdown("**어떤 차량을 찾고 계신가요?**")
        brands = data_loader.get_brands()
        cols = st.columns(3)
        for i, brand in enumerate(brands[:15]):
            with cols[i % 3]:
                if st.button(brand, key=f"brand_{brand}", use_container_width=True):
                    st.session_state.selected_brand = brand
                    st.session_state.step = 'model'
                    add_chat_message('user', brand)
                    add_chat_message('bot', f'{brand} 중 어떤 모델을 원하시나요?')
                    st.rerun()

    elif st.session_state.step == 'model':
        st.markdown(f"**{st.session_state.selected_brand} 중 어떤 모델을 원하시나요?**")
        models = data_loader.get_models(st.session_state.selected_brand)
        cols = st.columns(2)
        for i, model in enumerate(models):
            with cols[i % 2]:
                if st.button(model, key=f"model_{model}", use_container_width=True):
                    st.session_state.selected_model = model
                    st.session_state.step = 'grade'
                    add_chat_message('user', model)
                    add_chat_message('bot', f'{model}의 등급을 선택해주세요.')
                    st.rerun()

    elif st.session_state.step == 'grade':
        st.markdown(f"**{st.session_state.selected_model}의 등급을 선택해주세요.**")
        grades = data_loader.get_grades(st.session_state.selected_brand, st.session_state.selected_model)
        for grade in grades:
            if st.button(
                f"{grade['grade']} - {grade['price']:,.0f}원",
                key=f"grade_{grade['id_cargrade']}",
                use_container_width=True
            ):
                st.session_state.selected_car = grade
                st.session_state.step = 'product'
                add_chat_message('user', f"{grade['grade']} ({grade['price']:,.0f}원)")
                add_chat_message('bot', '리스와 렌트 중 어떤 상품을 원하시나요?')
                st.rerun()

    elif st.session_state.step == 'product':
        st.markdown("**리스와 렌트 중 어떤 상품을 원하시나요?**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("리스 (Lease)", key="product_lease", use_container_width=True):
                st.session_state.product_type = 'lease'
                st.session_state.step = 'period'
                add_chat_message('user', '리스')
                add_chat_message('bot', '계약기간은 얼마로 하시겠어요?')
                st.rerun()
        with col2:
            if st.button("렌트 (Rent)", key="product_rent", use_container_width=True):
                st.session_state.product_type = 'rent'
                st.session_state.step = 'period'
                add_chat_message('user', '렌트')
                add_chat_message('bot', '계약기간은 얼마로 하시겠어요?')
                st.rerun()

    elif st.session_state.step == 'period':
        st.markdown("**계약기간은 얼마로 하시겠어요?**")
        periods = [24, 36, 48, 60]
        cols = st.columns(len(periods))
        for i, period in enumerate(periods):
            with cols[i]:
                if st.button(f"{period}개월", key=f"period_{period}", use_container_width=True):
                    st.session_state.period = period
                    st.session_state.step = 'mileage'
                    add_chat_message('user', f'{period}개월')
                    add_chat_message('bot', '연간 주행거리는 어느 정도 예상하시나요?')
                    st.rerun()

    elif st.session_state.step == 'mileage':
        st.markdown("**연간 주행거리는 어느 정도 예상하시나요?**")
        if st.session_state.product_type == 'lease':
            mileages = ['1만km', '2만km', '3만km', '4만km']
        else:
            mileages = ['1만km', '2만km', '3만km', '무제한']
        cols = st.columns(len(mileages))
        for i, mileage in enumerate(mileages):
            with cols[i]:
                if st.button(mileage, key=f"mileage_{mileage}", use_container_width=True):
                    st.session_state.mileage = mileage
                    st.session_state.step = 'deposit_rate'
                    add_chat_message('user', mileage)
                    add_chat_message('bot', '보증금 또는 선납금을 설정하시겠어요?')
                    st.rerun()

    elif st.session_state.step == 'deposit_rate':
        st.markdown("**보증금 또는 선납금을 설정하시겠어요?**")
        cols = st.columns(4)
        rates = [0, 10, 20, 30]
        for i, rate in enumerate(rates):
            with cols[i]:
                label = "무보증 (0%)" if rate == 0 else f"{rate}%"
                if st.button(label, key=f"rate_{rate}", use_container_width=True):
                    st.session_state.deposit_rate = rate
                    if rate == 0:
                        st.session_state.deposit_type = '무보증'
                        st.session_state.step = 'dealer_discount'
                        add_chat_message('user', '무보증 (0%)')
                        add_chat_message('bot', '딜러 할인 금액을 입력해주세요 (만원 단위)')
                        st.rerun()
                    else:
                        st.session_state.step = 'deposit_type'
                        add_chat_message('user', f'{rate}%')
                        add_chat_message('bot', f'{rate}%를 어떻게 활용하시겠어요?')
                        st.rerun()

    elif st.session_state.step == 'deposit_type':
        st.markdown(f"**{st.session_state.deposit_rate}%를 어떻게 활용하시겠어요?**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"보증금 {st.session_state.deposit_rate}%", key="type_deposit", use_container_width=True):
                st.session_state.deposit_type = '보증금'
                st.session_state.step = 'dealer_discount'
                add_chat_message('user', f'보증금 {st.session_state.deposit_rate}%')
                add_chat_message('bot', '딜러 할인 금액을 입력해주세요 (만원 단위)')
                st.rerun()
        with col2:
            if st.button(f"선납금 {st.session_state.deposit_rate}%", key="type_advance", use_container_width=True):
                st.session_state.deposit_type = '선수금'
                st.session_state.step = 'dealer_discount'
                add_chat_message('user', f'선납금 {st.session_state.deposit_rate}%')
                add_chat_message('bot', '딜러 할인 금액을 입력해주세요 (만원 단위)')
                st.rerun()

    elif st.session_state.step == 'dealer_discount':
        st.markdown("**딜러 할인 금액을 입력해주세요 (만원 단위)**")
        st.markdown("*예: 100만원 할인시 100 입력, 할인 없으면 0 입력*")

        discount_input = st.number_input(
            "딜러 할인 (만원)",
            min_value=0,
            max_value=10000,
            value=0,
            step=10,
            key="discount_input"
        )

        if st.button("다음", key="confirm_discount", use_container_width=True):
            st.session_state.dealer_discount = discount_input * 10000  # 만원 → 원
            st.session_state.step = 'dealer_fee'
            add_chat_message('user', f'{discount_input}만원 할인')
            add_chat_message('bot', '딜러 Fee는 몇 %로 하시겠어요?')
            st.rerun()

    elif st.session_state.step == 'dealer_fee':
        st.markdown("**딜러 Fee는 몇 %로 하시겠어요?**")
        st.markdown("*일반적으로 0.5% ~ 2% 사이입니다*")

        fee_input = st.number_input(
            "딜러 Fee (%)",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.1,
            key="fee_input"
        )

        if st.button("다음", key="confirm_fee", use_container_width=True):
            st.session_state.dealer_fee_rate = fee_input
            st.session_state.step = 'option_price'
            add_chat_message('user', f'{fee_input}%')
            add_chat_message('bot', '추가 옵션 가격을 입력해주세요 (만원 단위)')
            st.rerun()

    elif st.session_state.step == 'option_price':
        st.markdown("**추가 옵션 가격을 입력해주세요 (만원 단위)**")
        st.markdown("*예: 500만원 옵션시 500 입력, 옵션 없으면 0 입력*")

        option_input = st.number_input(
            "옵션 가격 (만원)",
            min_value=0,
            max_value=5000,
            value=0,
            step=50,
            key="option_input"
        )

        if st.button("계산하기", key="confirm_option", use_container_width=True):
            st.session_state.option_price = option_input * 10000  # 만원 → 원
            st.session_state.step = 'calculate'
            add_chat_message('user', f'{option_input}만원 옵션')
            add_chat_message('bot', '계산 중입니다... ✓')
            st.rerun()

    # 초기화 버튼
    st.markdown("---")
    if st.button("🔄 처음부터 다시 시작", use_container_width=True):
        for key in ['step', 'chat_history', 'selected_brand', 'selected_model', 'selected_car',
                    'product_type', 'period', 'mileage', 'deposit_rate', 'deposit_type', 'results']:
            if key in st.session_state:
                del st.session_state[key]
        initialize_session_state()
        st.rerun()


def render_summary_ui():
    """중앙 요약/결과 UI"""
    st.markdown("### 📋 선택 요약 및 결과")

    if st.session_state.selected_car:
        st.markdown("#### 선택한 차량")
        st.info(f"""
**브랜드**: {st.session_state.selected_brand}
**모델**: {st.session_state.selected_model}
**등급**: {st.session_state.selected_car['grade']}
**가격**: {st.session_state.selected_car['price']:,.0f}원
**연료**: {st.session_state.selected_car['fuel_type']}
        """)

    if st.session_state.product_type:
        st.markdown("#### 금융 조건")
        deposit_info = f"{st.session_state.deposit_type} {st.session_state.deposit_rate}%" if st.session_state.deposit_rate is not None else "미선택"
        deposit_amount = st.session_state.selected_car['price'] * st.session_state.deposit_rate / 100 if st.session_state.deposit_rate else 0

        condition_text = f"""
**상품**: {'리스' if st.session_state.product_type == 'lease' else '렌트'}
**기간**: {st.session_state.period}개월 ({st.session_state.mileage})
**{st.session_state.deposit_type if st.session_state.deposit_type else '보증금'}**: {deposit_info}
{f"  └ {deposit_amount:,.0f}원" if deposit_amount > 0 else ""}
"""
        # 추가 입력값이 있으면 표시
        if st.session_state.step in ['calculate', 'option_price', 'dealer_fee', 'dealer_discount'] or st.session_state.results:
            if st.session_state.dealer_discount > 0:
                condition_text += f"**딜러 할인**: {st.session_state.dealer_discount:,.0f}원\n"
            if st.session_state.dealer_fee_rate:
                condition_text += f"**딜러 Fee**: {st.session_state.dealer_fee_rate}%\n"
            if st.session_state.option_price > 0:
                condition_text += f"**옵션 가격**: {st.session_state.option_price:,.0f}원\n"

        st.info(condition_text)

    if st.session_state.results:
        st.markdown("#### 월납입금 결과")
        st.success(f"총 {len(st.session_state.results)}개 금융사 견적")

        # 결과 테이블
        for i, result in enumerate(st.session_state.results[:10]):
            rank_class = ""
            if i == 0:
                rank_class = "rank-1"
            elif i == 1:
                rank_class = "rank-2"
            elif i == 2:
                rank_class = "rank-3"

            st.markdown(f"""
<div class="result-card {rank_class}">
    <strong>{i+1}위</strong> |
    <strong>{result['company']}</strong> |
    {result['payment_type']} |
    <strong style="color: #1976d2; font-size: 1.2em;">{result['monthly_payment']:,.0f}원</strong>
</div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.button("📞 상담 신청하기 (프로토타입: 비활성)", disabled=True, use_container_width=True)


def render_debug_ui():
    """우측 디버깅 UI"""
    st.markdown("### 🔍 계산 과정 상세")

    if st.session_state.results:
        for i, result in enumerate(st.session_state.results):
            with st.expander(f"{i+1}위. {result['company']} ({result['monthly_payment']:,.0f}원)"):
                debug = result['debug']

                st.markdown("**📊 기본 정보**")
                st.code(f"""
상품: {debug['product']}
금융사: {debug['company']}
기간: {debug['period']}개월
주행: {debug['mileage']}
결제 유형: {debug['payment_type']}
차량 가격: {debug['car_price']:,.0f}원
보증금/선납금: {debug['deposit_rate']}%
                """)

                st.markdown("**🧮 계산 단계**")
                for step in debug['steps']:
                    st.text(step)

                st.markdown("---")
                st.markdown("**📄 모델 파라미터**")
                st.json(debug['params'])

    else:
        st.info("차량과 조건을 선택하면 상세 계산 과정이 여기에 표시됩니다.")


def calculate_results():
    """계산 수행"""
    calculator = get_calculator()

    results = calculator.calculate_all_companies(
        car_price=st.session_state.selected_car['price'],
        product_type=st.session_state.product_type,
        period=st.session_state.period,
        mileage=st.session_state.mileage,
        deposit_rate=st.session_state.deposit_rate,
        payment_type=st.session_state.deposit_type,
        option_price=st.session_state.option_price,
        dealer_discount=st.session_state.dealer_discount,
        dealer_fee_rate=st.session_state.dealer_fee_rate / 100  # % → 소수
    )

    st.session_state.results = results


# ================ 모델 파라미터 페이지 ================

def render_params_page():
    """모델 파라미터 대시보드"""
    st.markdown('<div class="main-header">📊 모델 파라미터 대시보드</div>', unsafe_allow_html=True)

    calculator = get_calculator()
    params = calculator.params

    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["리스 파라미터", "렌트 파라미터", "파라미터 설명"])

    with tab1:
        render_product_params(params, 'lease', '리스')

    with tab2:
        render_product_params(params, 'rent', '렌트')

    with tab3:
        render_params_explanation()


def render_product_params(params, product_type, product_name):
    """상품별 파라미터 표시"""
    st.markdown(f"### {product_name} 금융사 파라미터")

    if product_type not in params:
        st.warning("파라미터 데이터가 없습니다.")
        return

    companies = list(params[product_type].keys())

    # 금융사 선택
    selected_company = st.selectbox(
        f"{product_name} 금융사 선택",
        companies,
        key=f"company_{product_type}"
    )

    if selected_company:
        company_data = params[product_type][selected_company]

        st.markdown(f"#### {selected_company} 상세 파라미터")

        # 조건별 파라미터를 테이블로 표시
        df_list = []
        for condition, param in company_data.items():
            df_list.append({
                '조건': condition,
                '기간': f"{param['period']}개월",
                '주행거리': param['mileage'],
                '기본요율 (%)': f"{param['base_rate']:.4f}",
                '옵션계수': f"{param['option_coefficient']:.6f}",
                '잔가율 (%)': f"{param['residual_rate']*100:.2f}",
                '샘플수': param['sample_count']
            })

        df = pd.DataFrame(df_list)
        st.dataframe(df, use_container_width=True)

        # 차트 표시
        st.markdown("#### 조건별 기본요율 비교")
        chart_data = pd.DataFrame({
            '조건': [d['조건'] for d in df_list],
            '기본요율': [float(d['기본요율 (%)']) for d in df_list]
        })
        st.bar_chart(chart_data.set_index('조건'))

        # 상세 JSON
        with st.expander("전체 파라미터 (JSON)"):
            st.json(company_data)


def render_params_explanation():
    """파라미터 설명"""
    st.markdown("### 📚 모델 파라미터 설명")

    st.markdown("""
#### 1. 기본요율 (base_rate)
- **의미**: 차량 가격 대비 월대여료 비율
- **단위**: % (예: 1.79% = 차량가 1억원 기준 월 179만원)
- **활용**: 기본 월대여료 = 차량가 × 기본요율 / 100

#### 2. 옵션계수 (option_coefficient)
- **의미**: 옵션 500만원당 월대여료 증가액
- **단위**: 원 (예: 0.0183 = 500만원 옵션시 월 18,300원 증가)
- **활용**: 옵션 가산액 = 옵션계수 × (옵션금액 / 5,000,000)

#### 3. 잔가율 (residual_rate)
- **의미**: 계약 종료 후 차량 잔존 가치 비율
- **단위**: 비율 (예: 0.57 = 57% 잔가)
- **특징**: 기간이 길고 주행거리가 많을수록 낮아짐

#### 4. 샘플수 (sample_count)
- **의미**: 해당 조건의 학습 데이터 개수
- **활용**: 샘플수가 많을수록 신뢰도 높음

---

### 📈 파라미터 추출 방법

1. **Excel 데이터 분석**: lease.xlsx, rent.xlsx 2,999개 차량 데이터
2. **패턴 추출**: 차량가격, 월대여료, 옵션 영향도 분석
3. **평균 계산**: 금융사별, 조건별 평균 파라미터 산출
4. **모델 생성**: JSON 형태로 저장 (model_params.json)

---

### 🔍 계산 예시

**조건**: 차량가 1억원, 36개월, 2만km, 무보증
**파라미터**: 기본요율 1.79%, 옵션계수 0.0183

```
기본 월대여료 = 100,000,000 × 1.79 / 100 = 1,790,000원
옵션 가산 = 0.0183 × (0 / 5,000,000) = 0원
딜러 Fee = 100,000,000 × 0.01 × 0.05 = 50,000원
────────────────────────────────────────────────
최종 월납입금 = 1,840,000원
```
    """)


# ================ 메인 ================

def main():
    """메인 함수"""
    initialize_session_state()
    render_sidebar()

    # 페이지 라우팅
    if st.session_state.page == 'calculator':
        render_calculator_page()
    elif st.session_state.page == 'params':
        render_params_page()


if __name__ == "__main__":
    main()
