import streamlit as st
import re

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="Транслитерация ПНАЭГ", page_icon="⚛️")

# Логотип РОСАТОМ (SVG в формате Base64 для отображения без внешних файлов)
logo_svg = """
<svg width="200" height="60" viewBox="0 0 200 60" xmlns="http://www.w3.org/2000/svg">
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial, sans-serif" font-weight="bold" font-size="24" fill="#005eb8">ROSATOM</text>
  <!-- Примечание: Это текстовая имитация логотипа. Для точного графического логотипа требуется файл изображения -->
  <path d="M10,30 Q20,10 30,30 T50,30" stroke="#005eb8" stroke-width="2" fill="none"/>
</svg>
"""

# Центрирование заголовка с логотипом
st.markdown(f"""
<div style="text-align: center;">
    {logo_svg}
</div>
""", unsafe_allow_html=True)

st.title("Транслитерация марок стали и сварочных материалов")

st.markdown("""
Конвертация марок стали и сварочных материалов в соответствии требованиями ПНАЭГ. 
Поддерживает ввод через запятую, точку с запятой, пробел или новую строку.
Для корректной транслитерации следует вводить марки стали соблюдая верхний регистр.
""")

# Списки, содержащие элементы для замены по химии

russian_elements = ["Х", "Н", "Т", "С", "В", "М", "Г", "К", "Д", "Ф", "Б", "Л", "Р", 
                    "х", "н", "т", "с", "в", "м", "г", "к", "д", "ф", "б", "л", "р"]
mendeleev_symbols = ["Cr", "Ni", "Ti", "Si", "Nb", "Mo", "Mn", "Co", "Cu", "V", "Nb", "L", "B",
                     "Cr", "Ni", "Ti", "Si", "Nb", "Mo", "Mn", "Co", "Cu", "V", "Nb", "L", "B"]

# Словарь исключений
extraordinary_grades_dict = {
    "10ГН2МФА-ВД*": "10MnNi2MoVA-VD*",
    "АМг6": "AlMg6",
    "БрАЖН10-4-4": "CuAlFeNi10-4-4",
    "БрАМц9-2": "CuAlMn9-2",
    "Сталь 20": "Steel 20",
    "Сталь 35": "Steel 35",
    "Сталь 45": "Steel 45",
    "ХН35ВТ": "CrNi35WTi",
    "ХН77ТЮР": "CrNi77TiAlB",
    "ПР-10Х18Н9М5С5Г4Б": "AP-10Cr18Ni9Mo5Si5Mn4Nb",
    "Урюпин": "Pitushara"
}

# Словарь фонетической транслитерации (без пробелов в значениях)
only_trans_map = dict(zip(
    [chr(i) for i in range(1040, 1104)],
    ["A","B","V","G","D","E","Zh","Z","I","Y","K","L","M","N","O","P","R","S","T","U","F","Kh","C","Ch","Sh","Shch","","Y","","E","Yu","Ya",
     "a","b","v","g","d","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","kh","ts","ch","sh","shch","","y","","e","yu","ya"]
))

# Словарь с приоритетом химической транслитерации
trans_map = dict(zip(
    [chr(i) for i in range(1040, 1104)],
    ["A","B","V","G","D","E","Zh","Z","I","Y","K","L","M","N","O","P","R","S","T","U","F","Kh","C","Ch","Sh","Shch","","Y","","E","Yu","Ya",
     "a","b","v","g","d","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","kh","ts","ch","sh","shch","","y","","e","yu","ya"]
))
trans_map.update(zip(russian_elements, mendeleev_symbols))

# --- ФУНКЦИИ ОБРАБОТКИ ---

def process_grade(grade):
    """
    Очищает строку: убирает пробелы по краям.
    Если это марка стали (не начинается со слова 'Сталь', 'Лист' и т.д.), 
    удаляет все внутренние пробелы.
    """
    grade = grade.strip()
    if not grade:
        return ""
        
    descriptive_starts = ("Сталь", "Круг", "Лист", "Труба", "Пруток", "Лак", "Смазка", "Состав", "Композиция")
    
    if grade.startswith(descriptive_starts):
        return " ".join(grade.split())
    else:
        return "".join(grade.split())

def transliterate_steel(grade):
    if grade in extraordinary_grades_dict:
        return extraordinary_grades_dict[grade]
    elif '-' in grade:
        dash_position = grade.index('-') # ищем разделитель, после которого пойдет фонетика
        part_1 = ''.join(trans_map.get(char, char) for char in grade[:dash_position]) # транслитерируем по химии
        part_2 = ''.join(only_trans_map.get(char, char) for char in grade[dash_position:]) # транслитерируем по фонетике
        return part_1 + part_2 # собираем, отдаем
    else:
        return ''.join(trans_map.get(char, char) for char in grade)

def transliterate_welding_material(grade):
    if '-' not in grade[3:]:
        return 'Sv-'+''.join(trans_map.get(char, char) for char in grade[3:])
    elif '(' in grade:
        prefix = 'Sv-' # отделяем префикс
        rest = grade[3:] # отделяем химию
        dash_position = rest.index('-') # ищем разделитель, после которого пойдет фонетика
        bracket_position = rest.index('(') # ищем разделитель, после которого пойдет доп.сварочный
        part_1 = ''.join(trans_map.get(char, char) for char in rest[:bracket_position]) # транслитерируем по химии
        part_2 = ''.join(only_trans_map.get(char, char) for char in rest[dash_position:bracket_position])
        if '-' in part_2: # транслитерируем по фонетике
            new_dash_position = part_2.index('-')
            part_3 = ''.join(trans_map.get(char, char) for char in rest[bracket_position+4:new_dash_position])
            part_4 = ''.join(only_trans_map.get(char, char) for char in rest[new_dash_position:])
            return prefix + part_1 + part_2 + '(' + prefix + part_3 + part_4
        else:
            part_2 = ''.join(trans_map.get(char, char) for char in rest[bracket_position+4:])
            return prefix + part_1 + '(' + prefix + part_2
    else:
        prefix = 'Sv-' # отделяем префикс
        rest = grade[3:] # отделяем химию
        dash_position = rest.index('-') # ищем разделитель, после которого пойдет фонетика
        part_1 = ''.join(trans_map.get(char, char) for char in rest[:dash_position]) # транслитерируем по химии
        part_2 = ''.join(only_trans_map.get(char, char) for char in rest[dash_position:]) # транслитерируем по фонетике
        return prefix + part_1 + part_2 # собираем, отдаем

def define_material(grade_list):
    new_grades_list = []
    original_clean_list = []
    
    for grade in grade_list:
        new_grade = process_grade(grade)
        if not new_grade:
            continue
            
        original_clean_list.append(new_grade)
        
        if new_grade in extraordinary_grades_dict:
            new_grades_list.append(extraordinary_grades_dict[new_grade])
            continue

        if new_grade[0].isdigit():
            new_grades_list.append(transliterate_steel(new_grade))
            continue
            
        if new_grade.startswith("Св"):
            new_grades_list.append(transliterate_welding_material(new_grade))
            continue
            
        new_grades_list.append(''.join(only_trans_map.get(char, char) for char in new_grade))
        
    return new_grades_list, original_clean_list

# --- ИНТЕРФЕЙС STREAMLIT ---

user_input = st.text_area(
    "Введите марки материалов:",
    placeholder="Примеры:\n10ГН2МФА, Св-08Г2С\n04 Х18Н10Т; БрАМц9-2\nСталь 20 15ГС",
    height=150,
    help="Можно использовать запятые, точки с запятой, пробелы или переносы строк в качестве разделителей."
)

if user_input:
    # Разбиваем ТОЛЬКО по запятым, точкам с запятой и новым строкам.
    # Пробелы внутри строк сохраняются, чтобы потом быть схлопнутыми функцией process_grade.
    raw_items = re.split(r'[,\;]+|\n+()', user_input)
    
    # Убираем пустые строки и лишние пробелы по краям каждого элемента
    original_input = [item.strip() for item in raw_items if item.strip()]
    
    if original_input:
        output, clean_originals = define_material(original_input)
        
        st.divider()
        st.subheader("Результаты обработки")
        
        project_choice = st.radio(
            "Выберите формат вывода:",
            ("Проект Эль-Дабаа (список)", "Проект Пакш (English[Russian])"),
            horizontal=True
        )
        
        result_text = ""
        
        if project_choice == "Проект Эль-Дабаа (список)":
            st.info("Формат: Перечисление через запятую")
            result_text = ', '.join(output)
            
        elif project_choice == "Проект Пакш (English[Russian])":
            st.info("Формат: English[ClearedRussian]")
            pairs = [f"{eng}({rus})" for eng, rus in zip(output, clean_originals)]
            result_text = ', '.join(pairs)
        
        st.code(result_text, language="text")
        st.success("Готово к копированию!")
        
        with st.expander("Показать таблицу соответствия"):
            import pandas as pd
            df = pd.DataFrame({
                "Оригинал (ввод)": original_input,
                "Очищенный оригинал": clean_originals,
                "Результат (EN)": output
            })
            st.dataframe(df, hide_index=True)

else:
    st.info("👆 Введите данные в поле выше.")

# Футер с новым текстом
st.markdown("---")
st.caption("ПЗМ ОМВиПД, ФАМ")
