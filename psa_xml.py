import pandas as pd
import xml.etree.ElementTree as ET
import yaml
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Union


# Function to dynamically extract attributes and children for CalcArrayItem
def extract_calc_item(item: ET.Element) -> Dict[str, Union[str, None]]:
    calc_item_data: Dict[str, Union[str, None]] = {
        "section": "CalcArrayItem",
        "index": item.get("index"),
        "CalcID": item.get("CalcID"),
    }

    calc = item.find("Calc")
    if calc is not None:
        # Extract attributes from Calc element dynamically
        for attr, value in calc.attrib.items():
            calc_item_data[attr] = value

        # Extract child elements dynamically
        for child in calc:
            if "value" in child.attrib:
                calc_item_data[child.tag] = child.attrib["value"]

    return calc_item_data


# Function to clean None values from nested dictionaries and lists
def delete_none(_dict: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    if isinstance(_dict, dict):
        for key, value in list(_dict.items()):
            if isinstance(value, (list, dict, tuple, set)):
                _dict[key] = delete_none(value)
            elif value is None or key is None:
                del _dict[key]
    elif isinstance(_dict, (list, set, tuple)):
        _dict = type(_dict)(delete_none(item) for item in _dict if item is not None)
    return _dict


# Function to handle the CalcArrayItems, parsing and modifying as needed
def process_calc_array(tree: ET.ElementTree, calc_array_tag: str) -> pd.DataFrame:
    calc_array = tree.find(calc_array_tag)
    data: List[Dict[str, Union[str, None]]] = []

    for item in calc_array.findall("CalcArrayItem"):
        data.append(extract_calc_item(item))

    df_calc = pd.DataFrame(data)
    df_calc = df_calc.set_index("index")
    df_calc_reset = df_calc.drop(
        df_calc[df_calc["FullName"].str.contains(", 2 ")].index
    ).reset_index(drop=True)

    return df_calc_reset


# Function to create XML elements for the CalcArrayItems and return the updated XML structure
def create_calc_array_xml(
    df_calc_reset: pd.DataFrame, calc_array_tag: str
) -> ET.Element:
    calcarray_root = ET.Element(
        calc_array_tag, attrib={"Size": str(df_calc_reset.shape[0])}
    )

    # Add CalcArrayItems back to the new element
    calc_attributes = ["UnitID", "Ordinal"]

    for index, row in df_calc_reset.iterrows():
        calc_item = ET.SubElement(
            calcarray_root,
            row["section"],
            attrib={"index": str(index), "CalcID": row["CalcID"]},
        )

        # Add child Calc element with attributes dynamically
        calc_attrs = {
            attr: str(row[attr]) for attr in calc_attributes if pd.notna(row[attr])
        }
        calc = ET.SubElement(calc_item, "Calc", calc_attrs)

        # Add dynamic child elements based on DataFrame columns
        for col in df_calc_reset.columns:
            if col not in ["section", "CalcID"] + calc_attributes and pd.notna(
                row[col]
            ):
                child = ET.SubElement(calc, col)
                child.set("value", str(row[col]))

    return calcarray_root


# Function to replace the old CalcArray in the XML tree
def replace_calc_array(
    root: ET.Element, new_calcarray_root: ET.Element, calc_array_tag: str
) -> ET.Element:
    calc_array_index: Union[int, None] = None
    for i, child in enumerate(root):
        if child.tag == calc_array_tag:
            calc_array_index = i
            root.remove(child)
            break

    if calc_array_index is None:
        calc_array_index = len(root)

    root.insert(calc_array_index, new_calcarray_root)

    return root


# Function to process the PSA file and return the updated XML tree
def process_psa_file(psa_file: str) -> ET.Element:
    with open(psa_file, "r") as file:
        lines: List[str] = file.readlines()
    filtered_lines: List[str] = [l for l in lines if not l.startswith("{{")]

    # Load XML content
    xmlElement = ET.fromstringlist(filtered_lines)
    tree = ET.ElementTree(xmlElement)
    root = tree.getroot()

    # Process CalcArray tags
    for calc_array_tag in [el.tag for el in root if el.tag.endswith("CalcArray")]:
        df_calc_reset = process_calc_array(tree, calc_array_tag)
        new_calcarray_root = create_calc_array_xml(df_calc_reset, calc_array_tag)
        root = replace_calc_array(root, new_calcarray_root, calc_array_tag)

    return root


# Function to write the modified XML tree back to a file
def write_psa_file(root: ET.Element, psa_file: str) -> None:
    ET.indent(root)
    pretty_xml_str: str = ET.tostring(
        root, encoding="unicode", method="xml", xml_declaration=True
    )
    pretty_xml_str = "{{# data}}\n" + pretty_xml_str + "\n\n{{/ data}}\n\n"

    file_out = Path("./psa_templates").joinpath(Path(psa_file).name)
    with open(file_out, mode="w", encoding="utf-8") as f:
        f.write(pretty_xml_str)


# Main function to iterate through all PSA files and process them
def main() -> None:
    psa_files_with_2_sensors: List[str] = [
        "psa_templates/MI_filterTemplate.psa",
        "psa_templates/MI_botsumTemplate_noO2.psa",
        "psa_templates/MI_datcnvTemplate_secO2.psa",
        "psa_templates/MI_datcnvTemplate_oneO2.psa",
        "psa_templates/MI_wildeditTemplate.psa",
        "psa_templates/MI_datcnvTemplate_noO2.psa",
        "psa_templates/MI_botsumTemplate_oneO2.psa",
        "psa_templates/MI_botsumTemplate_secO2.psa",
    ]

    for psa_file in psa_files_with_2_sensors:
        root = process_psa_file(psa_file)
        write_psa_file(root, psa_file)


if __name__ == "__main__":
    main()
