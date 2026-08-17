import json
import os
import shutil
import pandas as pd
from datetime import datetime

def parse_address(addr_str):
    if not addr_str or pd.isna(addr_str) or str(addr_str).strip() == '':
        return None
    parts = [p.strip() for p in str(addr_str).split(',') if p.strip()]
    if len(parts) == 4:
        return {'user_address_type': parts[0], 'user_tehsil': parts[1], 'user_district': parts[2], 'user_state': parts[3]}
    elif len(parts) == 3:
        return {'user_address_type': parts[0], 'user_tehsil': parts[1], 'user_district': '', 'user_state': parts[2]}
    elif len(parts) == 2:
        return {'user_address_type': parts[0], 'user_tehsil': '', 'user_district': '', 'user_state': parts[1]}
    elif len(parts) == 1:
        return {'user_address_type': parts[0], 'user_tehsil': '', 'user_district': '', 'user_state': ''}
    else:
        return {'user_address_type': parts[0], 'user_tehsil': parts[1], 'user_district': parts[2], 'user_state': ', '.join(parts[3:])}

def clean_val(val):
    if pd.isna(val) or val is None:
        return ''
    s = str(val).strip()
    if s.lower() == 'nan':
        return ''
    return s

def main():
    json_path = 'recipt_form_processed_receipts.json'
    backup_path = 'recipt_form_processed_receipts.backup.json'
    
    corr_path = '/home/manish/Downloads/SEERVI SAMAJ CORRECTION LIST-CORRECTION,SEERVI SAMAJ CORRECTION LIST-NEW ENTRIES,SEERVI SAMAJ C[...]/SEERVI SAMAJ CORRECTION LIST-CORRECTION.csv'
    new_path = '/home/manish/Downloads/SEERVI SAMAJ CORRECTION LIST-CORRECTION,SEERVI SAMAJ CORRECTION LIST-NEW ENTRIES,SEERVI SAMAJ C[...]/SEERVI SAMAJ CORRECTION LIST-NEW ENTRIES.csv'

    print("==================================================")
    print("🔄 RECEIPT JSON UPDATE & MERGE PROCESS")
    print("==================================================")

    # 1. Backup original JSON
    if os.path.exists(json_path):
        shutil.copyfile(json_path, backup_path)
        print(f"✅ Created backup file at: {backup_path}")

    # Load JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    initial_count = len(json_data)
    print(f"📊 Initial records in JSON: {initial_count}")

    # Create mapping by user_id
    user_map = {str(item['user_id']).strip(): item for item in json_data}

    # 2. Process CORRECTION CSV
    print(f"\n📂 Reading Correction CSV: {corr_path}")
    df_corr = pd.read_csv(corr_path, header=None)
    
    updated_users_count = 0
    updated_fields_count = 0

    for idx in range(2, len(df_corr)):
        row = df_corr.iloc[idx]
        user_id_raw = clean_val(row[0])
        if not user_id_raw or not user_id_raw.isdigit():
            continue
        
        user_id = str(int(user_id_raw))
        if user_id not in user_map:
            print(f"⚠️ User ID {user_id} from row {idx} not found in JSON database!")
            continue

        record = user_map[user_id]
        changes = []

        # Column 1: Firstname
        fn = clean_val(row[1])
        if fn != '' and fn != record.get('firstname'):
            changes.append(f"firstname: '{record.get('firstname')}' -> '{fn}'")
            record['firstname'] = fn
            updated_fields_count += 1

        # Column 2: Father
        father = clean_val(row[2])
        if father != '' and father != record.get('father'):
            changes.append(f"father: '{record.get('father')}' -> '{father}'")
            record['father'] = father
            updated_fields_count += 1

        # Column 3: Gotra
        gotra = clean_val(row[3])
        if gotra != '' and gotra != record.get('gotra'):
            changes.append(f"gotra: '{record.get('gotra')}' -> '{gotra}'")
            record['gotra'] = gotra
            updated_fields_count += 1

        # Column 4: Mobile Number
        mob = clean_val(row[4])
        if mob != '' and mob != record.get('mobile_number_1'):
            changes.append(f"mobile: '{record.get('mobile_number_1')}' -> '{mob}'")
            record['mobile_number_1'] = mob
            updated_fields_count += 1

        # Column 5: Mulnivas
        mulnivas = clean_val(row[5])
        if mulnivas != '':
            addr_dict = parse_address(mulnivas)
            if addr_dict:
                for k, v in addr_dict.items():
                    if record.get(k) != v:
                        changes.append(f"{k}: '{record.get(k)}' -> '{v}'")
                        record[k] = v
                        updated_fields_count += 1

        # Column 6: Vyaapar Name
        vyaapar_name = clean_val(row[6])
        if vyaapar_name != '' and vyaapar_name != record.get('vyaapar_name'):
            changes.append(f"vyaapar_name: '{record.get('vyaapar_name')}' -> '{vyaapar_name}'")
            record['vyaapar_name'] = vyaapar_name
            updated_fields_count += 1

        # Column 7: Vyaapar Tehsil (Business Address)
        vyaapar_tehsil = clean_val(row[7])
        if vyaapar_tehsil != '' and vyaapar_tehsil != record.get('vyaapar_tehsil'):
            changes.append(f"vyaapar_tehsil: '{record.get('vyaapar_tehsil')}' -> '{vyaapar_tehsil}'")
            record['vyaapar_tehsil'] = vyaapar_tehsil
            updated_fields_count += 1

        if changes:
            updated_users_count += 1
            print(f"✏️ Updated User ID {user_id}: {', '.join(changes)}")

    print(f"\n✅ Total corrected users: {updated_users_count} ({updated_fields_count} field changes)")

    # 3. Process NEW ENTRIES CSV
    print(f"\n📂 Reading New Entries CSV: {new_path}")
    df_new = pd.read_csv(new_path, header=None)

    current_date = datetime.now()
    formatted_date = "16/08/2026"
    formatted_datetime = current_date.strftime('%Y-%m-%d %H:%M:%S')

    new_entries_added = 0
    next_id = max([int(k) for k in user_map.keys() if k.isdigit()], default=0) + 1

    for idx in range(2, len(df_new)):
        row = df_new.iloc[idx]
        
        # Check if row has any non-empty data in cols 1..8
        row_vals = [clean_val(row[c]) for c in range(1, len(row))]
        if not any(row_vals):
            continue

        fn = clean_val(row[1])
        father = clean_val(row[2])
        gotra = clean_val(row[3])
        mob = clean_val(row[4])
        mulnivas = clean_val(row[5])
        vyaapar_name = clean_val(row[6])
        vyaapar_tehsil = clean_val(row[7])
        vyaapar_type = clean_val(row[8]) if len(row) > 8 else ''

        addr_dict = parse_address(mulnivas) if mulnivas else {'user_address_type': '', 'user_tehsil': '', 'user_district': '', 'user_state': ''}

        new_record = {
            'user_id': str(next_id),
            'firstname': fn,
            'father': father,
            'gotra': gotra,
            'user_address_type': addr_dict['user_address_type'],
            'user_tehsil': addr_dict['user_tehsil'],
            'user_district': addr_dict['user_district'],
            'user_state': addr_dict['user_state'],
            'mobile_number_1': mob,
            'vyaapar_name': vyaapar_name,
            'vyaapar_type': vyaapar_type,
            'vyaapar_tehsil': vyaapar_tehsil,
            'original_user_id': str(next_id),
            'receipt_number': next_id,
            'serial_number': next_id,
            'generation_date': formatted_datetime,
            'receipt_date': formatted_date,
            'current_date': formatted_date
        }

        json_data.append(new_record)
        user_map[str(next_id)] = new_record
        print(f"➕ Added New User ID {next_id}: {fn} ({gotra}) - {vyaapar_name}")

        next_id += 1
        new_entries_added += 1

    print(f"\n✅ Total new users added: {new_entries_added}")

    # 4. Save updated JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Successfully saved {len(json_data)} records to {json_path}")
    print(f"📊 Final Record Count: {len(json_data)} (Initial: {initial_count}, Added: {new_entries_added})")

if __name__ == '__main__':
    main()
