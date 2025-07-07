import os
import sys

if getattr(sys, 'frozen', False):
    # Running in a bundle
    app_path = os.path.join(sys._MEIPASS, 'Pool_Check_In.py')
else:
    # Running in normal Python
    app_path = 'Pool_Check_In.py'

os.system(f'streamlit run "{app_path}"')