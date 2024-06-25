import re
from typing import List, Tuple, Dict
from collections import defaultdict
from datetime import datetime

def find_datetime_positions(line: str) -> List[Tuple[int, int]]:
    pattern = r'\d{2}/\d{2} \d{2}:\d{2}'
    positions = [(m.start(), m.end()) for m in re.finditer(pattern, line)]
    print(f"Date-time positions found: {positions}")
    return positions

def process_special_table(table: List[str]) -> List[str]:
    print("Processing special table format...")
    output = []
    pattern = re.compile(r'^(.+?)\s{10,}(.+?)\((\d{8})\)$')
    
    for line in table[2:]:  # Skip the header lines
        match = pattern.match(line.strip())
        if match:
            item, result, date = match.groups()
            formatted_date = f"{date[:4]}/{date[4:6]}/{date[6:]}"
            output.append(f"[{formatted_date}] {item.strip()}:{result.strip()}")
    
    return output

def process_regular_table(table: List[str]) -> List[str]:
    print(f"Processing regular table with {len(table)} lines...")
    
    header = table[0]
    print(f"Header: {header}")
    data_lines = table[2:]  # Skip the separator line
    print(f"Number of data lines: {len(data_lines)}")

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

    print("Splitting tables...")
    for i, line in enumerate(lines):
        print(f"Line {i}: {line}")
        if header_pattern.match(line) or special_header_pattern.match(line):
            if current_table:
                tables.append(current_table)
                print(f"Added table with {len(current_table)} lines")
            current_table = [line]
        elif current_table:
            current_table.append(line)

    if current_table:
        tables.append(current_table)
        print(f"Added final table with {len(current_table)} lines")

    print(f"Total tables found: {len(tables)}")
    return tables

def process_report(report: str) -> str:
    print("Processing report...")
    tables = split_tables(report)
    all_results = []

    for i, table in enumerate(tables):
        print(f"Processing table {i+1}")
        try:
            if "檢驗(鏡檢,血清)項目:" in table[0]:
                table_results = process_special_table(table)
            else:
                table_results = process_regular_table(table)
            all_results.extend(table_results)
        except Exception as e:
            print(f"Error processing table {i+1}: {e}")

    return '\n'.join(all_results)