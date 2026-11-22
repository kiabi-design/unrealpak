EXTRACTION KIT FOR PS4 RUSSIAN VOICE MOD
=========================================

СОДЕРЖИМОЕ ПАПКИ:
-----------------
extract_english_wem_from_ps4.py      # Скрипт 1: достать 536 английских .wem из PS4 pakchunk2
extract_russian_uassets_from_pc.py   # Скрипт 2: достать русские .uasset из PC мода GameVoice
extract_all_russian_wem_from_pc.py   # Скрипт 3 (альтернатива): достать ВСЕ 536 русских .wem из PC мода
pak_filelist.txt                     # Список файлов PS4 pakchunk2 (нужен для скрипта 1)
pak_replacements.json                # План замены 364 файлов (нужен для скрипта 1)
ps4_pakchunk2_wwise_to_offset.json   # Маппинг Wwise ID -> offset (справка)
oo2core_9_win64.dll                  # Oodle библиотека для распаковки (Windows)

---

ЧТО НУЖНО СДЕЛАТЬ (НА ТВОЕЙ СТОРОНЕ):
====================================

ВАРИАНТ А (рекомендуемый) — используя PS4 pakchunk2 + PC мод:
------------------------------------------------------------
1. Положи рядом с скриптами:
   - pakchunk2-ps4.pak (815 MB, твой PS4 файл)
   - Папку extracted_PC/ с распакованным PC модом GameVoice
     (pakchunk0-WindowsNoEditor_8/9-GV-RU_P.utoc/.ucas)

2. Запусти скрипт 1 (Python 3):
   python extract_english_wem_from_ps4.py
   -> Создаст папку extracted_english_wem/ с 536 .wem файлами

3. Запусти скрипт 2 (на Windows, нужен oo2core_9_win64.dll):
   python extract_russian_uassets_from_pc.py
   -> Создаст папку extracted_russian_uassets/ с ~38 .uasset файлами

4. Скинь мне эти ДВЕ папки (они весят МБ, не ГБ)

---

ВАРИАНТ Б (альтернатива) — всё из PC мода:
------------------------------------------
Если проще работать только с PC модом:
1. Положи папку extracted_PC/ с PC модом
2. Запусти скрипт 3 (на Windows):
   python extract_all_russian_wem_from_pc.py
   -> Создаст extracted_russian_wem_all/ с 536 русскими .wem
3. Запусти скрипт 2 для .uasset
4. Скинь мне две папки

---

ЧТО Я СДЕЛАЮ ПОСЛЕ ПОЛУЧЕНИЯ ФАЙЛОВ:
====================================
1. Соберу правильный pakchunk2-ps4.pak с 536 реальными русскими .wem
2. Соберу правильный pakchunk0-ps4.pak с реальными русскими .uasset (тексты/субтитры/шрифты)
3. Создам .utoc/.ucas для обоих чанков (IoStore формат PS4)
4. Отдашь 6 файлов для установки на PS4:
   - pakchunk0-ps4.pak / .utoc / .ucas
   - pakchunk2-ps4_russian.pak / .utoc / .ucas

---

ТРЕБОВАНИЯ:
-----------
- Python 3.8+
- pycryptodome (для скрипта 3): pip install pycryptodome
- Windows (для Oodle DLL) или Linux с рабочим liboo2core_9.so

---

ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ:
------------------------
- Скрипт 1 не находит файлы -> проверь путь к pakchunk2-ps4.pak в скрипте
- Скрипт 2/3 падают на Oodle -> убедись что oo2core_9_win64.dll рядом со скриптом
- Файлов мало -> проверь что PC мод распакован в extracted_PC/Paks/

ПИШИ ЕСЛИ ВОЗНИКНУТ ПРОБЛЕМЫ!