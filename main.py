import datetime
from dateutil.relativedelta import relativedelta

import streamlit as st
import pandas as pd


def upload_file():
    uploaded_file = st.sidebar.file_uploader("뱅크 샐러드 엑셀 파일 업로드", type=['xlsx'])

    if uploaded_file is not None:
        origin_df = None
        try:
            origin_df = pd.read_excel(uploaded_file, sheet_name="가계부 내역")
        except Exception as e:
            st.error(f"파일을 읽을 수 없습니다. : ${e}")
            return pd.DataFrame()

        return origin_df
    return None


def set_date_range():
    today = datetime.datetime.now()

    select_date_range = st.sidebar.selectbox(
        "조회 기간",
        ["한달 전", "일주일 전"]
    )

    date_range = None

    if select_date_range == "한달 전":
        date_range = get_date_range(today, offset=1, date_type='month')
    elif select_date_range == "일주일 전":
        date_range = get_date_range(today, offset=1, date_type='week')

    date_range = st.sidebar.date_input(
        '조회 기간',
        value=date_range if date_range is not None else (today, today),
        format='YYYY-MM-DD'
    )

    return date_range


def set_payment_list(df):
    exception_list = ["학교 계좌", "자유적금"]
    payment_lists = [v for v in df['결제수단'].unique().tolist() if v not in exception_list]
    options = []

    credit_list = st.sidebar.multiselect(
        '다음 중 신용카드 목록을 골라주세요.',
        payment_lists
    )

    pay_card_list = st.sidebar.multiselect(
        '다음 중 체크카드 또는 현금 결제 목록을 골라주세요.',
        payment_lists
    )

    if not credit_list and not pay_card_list:
        options = st.sidebar.multiselect(
            '보고 싶은 결제수단을 골라주세요.',
            payment_lists
        )

    return options, credit_list, pay_card_list


def make_new_df(origin: pd.DataFrame, date_range):
    start = date_range[0].strftime("%Y-%m-%d")
    end = date_range[1].strftime("%Y-%m-%d")
    df = pd.DataFrame(columns=['날짜', '거래처', '금액', '분류', '결제수단', '유용성 여부(사용자 선택)'])
    filtered_df = origin[(origin['날짜'] >= start) & (origin['날짜'] <= end)]

    df['날짜'] = filtered_df['날짜']
    df['거래처'] = filtered_df['내용']
    df['금액'] = abs(filtered_df['금액'])
    df['결제수단'] = filtered_df['결제수단']
    df['분류'] = filtered_df['대분류']

    return df


def calculate_non_usable(df, credit_list=None, pay_card_list=None):
    twitch = df[(df['거래처'].isin(['Twip', '다날_정보서비스']))]
    twitch_credit = twitch[twitch['결제수단'].isin(credit_list)]['금액']
    twitch_pay = twitch[twitch['결제수단'].isin(pay_card_list)]['금액']
    food = df[df['거래처'].isin(['(주)우아한형제들', '요기요', '요기요_간편결제'])]
    food_credit = food[food['결제수단'].isin(credit_list)]['금액']
    print(food)
    print(food_credit)
    food_pay = food[food['결제수단'].isin(pay_card_list)]['금액']

    return {
        'twitch': {
            "전체": sum(twitch['금액']),
            "신용카드": sum(twitch_credit),
            "체크카드 및 계좌이체": sum(twitch_pay)
        },
        'food': {
            "전체": sum(food['금액']),
            "신용카드": sum(food_credit),
            "체크카드 및 계좌이체": sum(food_pay)
        },
    }


def get_date_range(start, offset, date_type='month'):
    end = start
    if date_type == 'month':
        end = start - relativedelta(months=offset)
    elif date_type == 'week':
        end = start - relativedelta(weeks=offset)
    return end, start


def set_results(df, credit_list, pay_card_list, date_range):
    st.header("조회 데이터 정보")
    st.write(f"조회 기간 : {date_range[0]} ~ {date_range[1]}")
    st.dataframe(df)

    st.header("이번달 사용된 불필요해보이는 목록이에요.")
    non_usable = calculate_non_usable(df, credit_list, pay_card_list)
    st.subheader("Twitch에 사용된 금액이에요.")
    for k, v in non_usable['twitch'].items():
        st.write(f"{k} 금액 : {v}")
    st.subheader("식대에 사용된 금액이에요.")
    for k, v in non_usable['food'].items():
        st.write(f"{k} 금액 : {v}")


def init_sidebar():
    st.sidebar.title("가계부 설정 메뉴")

    st.sidebar.subheader("뱅크 샐러드 파일 업로드")
    file = upload_file()

    st.sidebar.subheader("조회 기간 설정")
    date_range = set_date_range()

    if file is not None:
        df = make_new_df(file, date_range)

        options, credit_list, pay_card_list = set_payment_list(df)

        if len(options) != 0:
            df = df[df['결제수단'].isin(options)]

        df_visible = st.sidebar.button("조회")

        if df_visible:
            set_results(df, credit_list, pay_card_list, date_range)

    else:
        st.info("가계부 파일이 없습니다. 파일을 넣어주세요!")


init_sidebar()



