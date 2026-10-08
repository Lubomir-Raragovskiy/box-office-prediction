import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from pypmml import Model

# Функція для автоматичного витягування категорій з XML-файлу моделі
@st.cache_data
def extract_categories(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    categories = {}
    
    # Шукаємо всі поля DataField з атрибутом categorical
    for data_field in root.findall('.//DataField'):
        if data_field.get('optype') == 'categorical':
            name = data_field.get('name')
            values = [val.get('value') for val in data_field.findall('Value')]
            categories[name] = values
            
    return categories

# Завантаження моделі та її категорій
@st.cache_resource
def load_model():
    # Завантажуємо виправлений за всіма стандартами файл моделі
    return Model.fromFile('model.xml')

model = load_model()
categories = extract_categories('model.xml')

# Допоміжна функція для безпечного пошуку індексу значення за замовчуванням
def get_default_index(options_list, default_value):
    try:
        return options_list.index(default_value)
    except ValueError:
        return 0

st.set_page_config(page_title="Box Office Predictor", layout="wide")

st.title("🎬 Прогнозування касових зборів фільмів")
st.markdown("Введіть характеристики фільму. Текстові категорії підтягуються безпосередньо з бази даних моделі.")

# Розділяємо інтерфейс на дві колонки
col1, col2 = st.columns(2)

with col1:
    st.subheader("Фінансові та технічні дані")
    budget = st.number_input("Бюджет (Budget) $", min_value=0.0, value=50000000.0, step=1000000.0, format="%f")
    imdb = st.number_input("Рейтинг IMDb", min_value=0.0, max_value=10.0, value=7.0, step=0.1)
    actor_box_office = st.number_input("Actors Box Office %", value=0.0, step=1.0)
    director_box_office = st.number_input("Director Box Office %", value=0.0, step=1.0)
    
    # Тривалість як ціле число
    runtime = st.number_input("Тривалість у хв (Running time)", min_value=0, value=120, step=1)
    
    # Селектбокс для жанру
    genre_opts = categories.get("Genre", ["Action"])
    genre = st.selectbox("Жанр (Genre)", genre_opts, index=get_default_index(genre_opts, "Action"))

with col2:
    st.subheader("Знімальна група та нагороди")
    # Селектбокси для режисера та акторів
    dir_opts = categories.get("Director", ["James Cameron"])
    director = st.selectbox("Режисер (Director)", dir_opts, index=get_default_index(dir_opts, "James Cameron"))
    
    act1_opts = categories.get("Actor 1", ["Leonardo DiCaprio"])
    actor1 = st.selectbox("Актор 1 (Actor 1)", act1_opts, index=get_default_index(act1_opts, "Leonardo DiCaprio"))
    
    act2_opts = categories.get("Actor 2", ["Kate Winslet"])
    actor2 = st.selectbox("Актор 2 (Actor 2)", act2_opts, index=get_default_index(act2_opts, "Kate Winslet"))
    
    act3_opts = categories.get("Actor 3", ["Matt Damon"])
    actor3 = st.selectbox("Актор 3 (Actor 3)", act3_opts, index=get_default_index(act3_opts, "Matt Damon"))
    
    # Нагороди як цілі числа
    oscar_nom = st.number_input("Номінації на Оскар/Глобус", min_value=0, value=0, step=1)
    oscar_aw = st.number_input("Перемоги на Оскар/Глобус", min_value=0, value=0, step=1)

st.markdown("---")

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
with col_btn2:
    predict_clicked = st.button("🚀 Прогнозувати касові збори", use_container_width=True)

if predict_clicked:
    # 1. Збираємо всі введені дані у словник
    raw_input_dict = {
        "Budget": budget,
        "Actors Box Office %": actor_box_office,
        "Director Box Office %": director_box_office,
        "IMDb score": imdb,
        "Director": director,
        "Running time": runtime,
        "Actor 1": actor1,
        "Actor 2": actor2,
        "Actor 3": actor3,
        "Genre": genre,
        "Oscar and Golden Globes nominations": oscar_nom,
        "Oscar and Golden Globes awards": oscar_aw
    }
    
    try:
        # 2. Вишиковуємо дані у СТРОГОМУ порядку, якого очікує модель
        ordered_input = {}
        for name in model.inputNames:
            if name in raw_input_dict:
                ordered_input[name] = raw_input_dict[name]
                
        # Створюємо DataFrame з правильним порядком колонок
        input_data = pd.DataFrame([ordered_input])
        
        # 3. Виконуємо прогноз
        result = model.predict(input_data)
        
        # 4. Витягуємо результат
        target_col = None
        
        target_col = result.columns[0]
            
        predicted_value = result.iloc[0][target_col]
            
        # Відображення результату
        if pd.isna(predicted_value):
            st.error("Результат: NaN. Модель не змогла обробити ці дані.")
        else:
            st.success(f"Прогнозовані касові збори: **${predicted_value:,.2f}**")
            
    except Exception as e:
        st.error(f"Виникла помилка під час прогнозування: {e}")