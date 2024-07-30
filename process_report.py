import re
from typing import List, Tuple, Dict
from collections import defaultdict
from datetime import datetime

def find_datetime_positions(line: str) -> List[Tuple[int, int]]:
    pattern = r'\d{2}/\d{2} \d{2}:\d{2}'
    positions = [(m.start(), m.end()) for m in re.finditer(pattern, line)]
    # print(f"Date-time positions found: {positions}")
    return positions

def process_special_table_original(table: List[str]) -> List[str]:
    output = []
    pattern = re.compile(r'^(.+?)\s{10,}(.+?)\((\d{8})\)$')
    
    for line in table[2:]:  # Skip the header lines
        match = pattern.match(line.strip())
        if match:
            item, result, date = match.groups()
            formatted_date = f"{date[:4]}/{date[4:6]}/{date[6:]}"
            output.append(f"[{formatted_date}] {item.strip()}:{result.strip()}")
    
    return output

def process_special_table_new(table: List[str]) -> List[str]:
    # print("Processing special table with new format...")
    output = []
    pattern = re.compile(r'^(.+?)\s{10,}(.+?)\((\d{8})\)$')
    
    urine_strip_items = []
    urine_sediment_items = []
    current_date = None
    urine_strip_keys = set(['Occult Blood', 'Ketone', 'Nitrite', 'Leucocyte esterase', 'Color', 'Turbidity', 'Glucose', 'Protein', 'Bilirubin', 'Urobilinogen', 'pH', 'Sp.gr'])
    urine_sediment_keys = set(['Cast', 'RBC', 'WBC', 'EP.cell', 'Bacteria', 'Yeast', 'Trichomonas', 'Sperm', 'Crystal'])

    def flush_current_section():
        nonlocal urine_strip_items, urine_sediment_items, current_date, output
        if urine_strip_items:
            output.append(f"[{current_date}] Urine strip: {', '.join(urine_strip_items)}")
            urine_strip_items = []
        if urine_sediment_items:
            output.append(f"[{current_date}] Urine sediment: {', '.join(urine_sediment_items)}")
            urine_sediment_items = []

    for line in table[2:]:  # Skip the header lines
        match = pattern.match(line.strip())
        if match:
            item, result, date = match.groups()
            item = item.strip()
            result = result.strip()
            formatted_date = f"{date[:4]}/{date[4:6]}/{date[6:]}"

            if formatted_date != current_date:
                flush_current_section()
                current_date = formatted_date

            if item == 'Urine strip' or item == 'Urine sediment':
                # Skip these lines as they are just headers
                continue
            elif item in urine_strip_keys and result != '-':
                urine_strip_items.append(f"{item}:{result}")
            elif item in urine_sediment_keys and result != '-':
                urine_sediment_items.append(f"{item}:{result}")
            elif result not in ['***', '-']:  # Skip lines with '***' or '-' as the result
                flush_current_section()
                output.append(f"[{formatted_date}] {item}:{result}")

    flush_current_section()  # Flush any remaining items
    
    return output

def process_report(report: str, use_abbreviations: bool = False, use_new_format: bool = False) -> str:
    # print("Processing report...")
    tables = split_tables(report)
    all_results = []

    for i, table in enumerate(tables):
        # print(f"Processing table {i+1}")
        try:
            if "檢驗(鏡檢,血清)項目:" in table[0]:
                if use_new_format:
                    table_results = process_special_table_new(table)
                else:
                    table_results = process_special_table_original(table)
            else:
                table_results = process_regular_table(table)
            all_results.extend(table_results)
        except Exception as e:
            print(f"Error processing table {i+1}: {e}")

    result = '\n'.join(all_results)
    
    if use_abbreviations:
        result = apply_abbreviations(result)
    
    return result

def process_regular_table(table: List[str]) -> List[str]:
    # print(f"Processing regular table with {len(table)} lines...")
    
    header = table[0]
    # print(f"Header: {header}")
    data_lines = table[2:]  # Skip the separator line
    # print(f"Number of data lines: {len(data_lines)}")

    datetime_positions = find_datetime_positions(header)
    
    result: Dict[str, List[str]] = defaultdict(list)
    
    for line in data_lines:
        item = line[:datetime_positions[0][0]].strip()
        if not item or item == '_' * len(item):
            continue
        
        for i, (start, end) in enumerate(datetime_positions):
            datetime_str = header[start:end].strip()
            value = line[start:end].strip()
            
            if value and value != '***':
                result[datetime_str].append(f"{item} {value}")
    
    output = []
    for dt in sorted(result.keys(), key=lambda x: datetime.strptime(x, "%m/%d %H:%M")):
        output.append(f"[{dt}] {' '.join(result[dt])}")
    
    return output

def split_tables(report: str) -> List[List[str]]:
    lines = report.strip().split('\n')
    tables = []
    current_table = []
    header_pattern = re.compile(r'Name\s+(\d{2}/\d{2} \d{2}:\d{2}\s*)+')
    special_header_pattern = re.compile(r'檢驗\(鏡檢,血清\)項目:')

    # print("Splitting tables...")
    for i, line in enumerate(lines):
        print(f"Line {i}: {line}")
        if header_pattern.match(line) or special_header_pattern.match(line):
            if current_table:
                tables.append(current_table)
                # print(f"Added table with {len(current_table)} lines")
            current_table = [line]
        elif current_table:
            current_table.append(line)

    if current_table:
        tables.append(current_table)
        # print(f"Added final table with {len(current_table)} lines")

    # print(f"Total tables found: {len(tables)}")
    return tables

def apply_abbreviations(text: str) -> str:
    abbreviations = {
        'Lymphocyte': 'Lym',
        'Monocyte': 'Mono',
        'Eosinophil': 'Eos',
        'Basophil': 'Baso',
        'Platelet': 'PLT',
        'Creatinine': 'Cr',
        'K mmol/L': 'K',
        'estimated Ccr(MDRD)': 'eCcr(MDRD)'
    }
    
    for full, abbr in abbreviations.items():
        text = text.replace(full, abbr)
    
    return text
