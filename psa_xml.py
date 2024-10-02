import pandas as pd
import xml.etree.ElementTree as ET
import yaml
import numpy as np

def main():
    with open('psa_templates/MI_datcnvTemplate_oneO2.psa', 'r') as file:
    # with open('psa_templates/MI_datcnvTemplate_secO2.psa', 'r') as file:
        lines = file.readlines()
    filtered_lines = [l_i for l_i in lines if not l_i.startswith('{{')]
    # Load the XML file
    tree = ET.fromstringlist(filtered_lines)
    root = ET.ElementTree(tree)

    # Initialize a list to store data for the dataframe
    data = []

    # Track all parsed tags for completeness check
    parsed_tags = set()

    # Function to extract CalcArrayItem details
    def extract_calc_item(item):
        parsed_tags.add('CalcArrayItem')
        calc = item.find('Calc')
        return {
            'section': 'CalcArrayItem',
            'index': item.get('index'),
            'CalcID': item.get('CalcID'),
            'UnitID': calc.get('UnitID'),
            'Ordinal': calc.get('Ordinal'),
            'FullName': calc.find('FullName').get('value'),
            'Latitude': calc.find('Latitude').get('value') if calc.find('Latitude') is not None else None,
            'ApplyHysteresisCorrection': calc.find('ApplyHysteresisCorrection').get('value') if calc.find('ApplyHysteresisCorrection') is not None else None,
            'ApplyTauCorrection': calc.find('ApplyTauCorrection').get('value') if calc.find('ApplyTauCorrection') is not None else None
        }

    # Parse CalcArrayItems
    calc_array = root.find('CalcArray')
    for item in calc_array.findall('CalcArrayItem'):
        data.append(extract_calc_item(item))
    
    calc_items = data[:]

    # Parse other single value elements
    single_value_elements = [
        'Version', 'ServerName', 'InstrumentPath', 'InstrumentMatch', 'InputDir',
        'OutputDir', 'NameAppend', 'OutputFile', 'LastProcessed', 'ProcessScansToEnd',
        'ScansToSkip', 'ScansToProcess', 'MergeHeaderFile', 'OutputFormat', 'FromCast',
        'CreateFile', 'ScanRangeSource', 'ScanRangeOffset', 'ScanRangeDuration',
        'StartTimeOption', 'PromptForNoteAndOrStartTime'
    ]

    for elem in single_value_elements:
        el = root.find(elem)
        if el is not None:
            data.append({
                'section': 'SingleElement',
                'name': elem,
                'value': el.get('value')
            })
            parsed_tags.add(elem)

    # Parse MiscellaneousDataForCalculations section
    misc_section = root.find('MiscellaneousDataForCalculations')
    if misc_section is not None:
        parsed_tags.add('MiscellaneousDataForCalculations')
        misc_data = {
            'section': 'MiscellaneousDataForCalculations',
            'Latitude': misc_section.find('Latitude').get('value'),
            'Longitude': misc_section.find('Longitude').get('value'),
        }
        descent_rate = misc_section.find('DescentRateAndAcceleration')
        if descent_rate is not None:
            misc_data['DescentRate_WindowSize'] = descent_rate.find('WindowSize').get('value')

        oxygen = misc_section.find('Oxygen')
        if oxygen is not None:
            misc_data['Oxygen_WindowSize'] = oxygen.find('WindowSize').get('value')
            misc_data['ApplyHysteresisCorrection'] = oxygen.find('ApplyHysteresisCorrection').get('value')
            misc_data['ApplyTauCorrection'] = oxygen.find('ApplyTauCorrection').get('value')

        avg_sound_velocity = misc_section.find('AverageSoundVelocity')
        if avg_sound_velocity is not None:
            misc_data['AverageSoundVelocity_MinimumPressure'] = avg_sound_velocity.find('MinimumPressure').get('value')
            misc_data['AverageSoundVelocity_MinimumSalinity'] = avg_sound_velocity.find('MinimumSalinity').get('value')
            misc_data['AverageSoundVelocity_PressureWindowSize'] = avg_sound_velocity.find('PressureWindowSize').get('value')
            misc_data['AverageSoundVelocity_TimeWindowSize'] = avg_sound_velocity.find('TimeWindowSize').get('value')

        data.append(misc_data)

    # Parse InputFileArray
    input_file_array = root.find('InputFileArray')
    if input_file_array is not None:
        parsed_tags.add('InputFileArray')
        array_items = input_file_array.findall('ArrayItem')
        for array_item in array_items:
            data.append({
                'section': 'InputFileArray',
                'index': array_item.get('index'),
                'value': array_item.get('value')
            })

    # Convert the data list to a pandas DataFrame
    df = pd.DataFrame(data)

    # List of all expected tags in the XML (adjust this according to your actual XML structure)
    expected_tags = {
        'Version', 'ServerName', 'InstrumentPath', 'InstrumentMatch', 'InputDir',
        'OutputDir', 'NameAppend', 'OutputFile', 'LastProcessed', 'ProcessScansToEnd',
        'ScansToSkip', 'ScansToProcess', 'MergeHeaderFile', 'OutputFormat', 'FromCast',
        'CreateFile', 'ScanRangeSource', 'ScanRangeOffset', 'ScanRangeDuration',
        'StartTimeOption', 'PromptForNoteAndOrStartTime', 'CalcArrayItem', 
        'MiscellaneousDataForCalculations', 'InputFileArray'
    }

    # Issue a warning if not everything is parsed
    missing_tags = expected_tags - parsed_tags
    if missing_tags:
        warnings.warn(f"The following tags were not parsed into the DataFrame: {', '.join(missing_tags)}")
    
    
    def delete_none(_dict):
        """Delete None values recursively from all of the dictionaries, tuples, lists, sets"""
        if isinstance(_dict, dict):
            for key, value in list(_dict.items()):
                if isinstance(value, (list, dict, tuple, set)):
                    _dict[key] = delete_none(value)
                elif value is None or key is None:
                    del _dict[key]

        elif isinstance(_dict, (list, set, tuple)):
            _dict = type(_dict)(delete_none(item) for item in _dict if item is not None)

        return _dict

    filtered_dict = delete_none(df.replace({np.nan: None}).to_dict(orient="records"))
    with open("/tmp/output.yaml", "w") as file:
        yaml.dump(filtered_dict, file, default_flow_style=False)


    df_calc = pd.DataFrame(calc_items)
    df_calc = df_calc.set_index("index")
    df_calc_reset = df_calc.drop(df_calc[df_calc["FullName"].str.contains(", 2 ")].index).reset_index(drop=True)

    # Create the root XML element
    calcarray_root = ET.Element('CalcArray')

    # Columns that should be used as attributes of the 'Calc' element
    calc_attributes = ['CalcID', 'UnitID', 'Ordinal']

    # Iterate through DataFrame rows and create XML elements
    for index, row in df_calc_reset.iterrows():
        # Create a CalcArrayItem element
        calc_item = ET.SubElement(calcarray_root, row['section'], {'index': str(index)})

        # Add child Calc element
        calc_attrs = {attr: str(row[attr]) for attr in calc_attributes if pd.notna(row[attr])}
        calc = ET.SubElement(calc_item, 'Calc', calc_attrs)

        # Add other columns dynamically
        for col in df_calc_reset.columns:
            if col not in ['section'] + calc_attributes and pd.notna(row[col]):
                # Create an element with column name as tag, value as attribute
                child = ET.SubElement(calc, col)
                child.set('value', str(row[col]))

    
    ET.indent(calcarray_root)
    pretty_xml_str = ET.tostring(calcarray_root, encoding='unicode', method='xml')
    pass


if __name__ == "__main__":
    main()
    