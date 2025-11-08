#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from datetime import datetime
import os

excel_file = 'excel/Gesamttabelle.xlsx'

df = pd.read_excel(excel_file, sheet_name='Gesamttabelle')


os.makedirs('exports', exist_ok=True)


timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
csv_filename = f'exports/Gesamttabelle_Python.csv'


df.to_csv(csv_filename, sep=';', index=False, encoding='utf-8-sig')
