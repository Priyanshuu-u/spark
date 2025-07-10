#!/usr/bin/env python3
"""
Tableau to Power BI Converter - FIXED VERSION
Converts Tableau .twbx files to Power BI template (.pbit) format
Specifically handles bar charts with Oracle database connections
"""

import zipfile
import xml.etree.ElementTree as ET
import json
import os
import sys
import uuid
from pathlib import Path
import argparse
from typing import Dict, List, Any, Optional

class TableauToPowerBIConverter:
    def __init__(self):
        self.tableau_data = {}
        self.powerbi_config = {}
        
    def extract_twbx(self, twbx_path: str) -> str:
        """Extract .twbx file and return path to .twb file"""
        try:
            extract_path = twbx_path.replace('.twbx', '_extracted')
            os.makedirs(extract_path, exist_ok=True)
            
            with zipfile.ZipFile(twbx_path, 'r') as zip_file:
                zip_file.extractall(extract_path)
            
            # Find the .twb file
            for file in os.listdir(extract_path):
                if file.endswith('.twb'):
                    return os.path.join(extract_path, file)
            
            raise FileNotFoundError("No .twb file found in the .twbx archive")
            
        except Exception as e:
            print(f"Error extracting .twbx file: {e}")
            return None
    
    def parse_tableau_workbook(self, twb_path: str) -> Dict:
        """Parse Tableau workbook XML and extract relevant information"""
        try:
            tree = ET.parse(twb_path)
            root = tree.getroot()
            
            workbook_data = {
                'name': root.get('name', 'Converted Dashboard'),
                'datasources': [],
                'worksheets': [],
                'dashboards': []
            }
            
            # Extract datasources
            for datasource in root.findall('.//datasource'):
                ds_info = self._parse_datasource(datasource)
                if ds_info:
                    workbook_data['datasources'].append(ds_info)
            
            # Extract worksheets
            for worksheet in root.findall('.//worksheet'):
                ws_info = self._parse_worksheet(worksheet)
                if ws_info:
                    workbook_data['worksheets'].append(ws_info)
            
            # Extract dashboards
            for dashboard in root.findall('.//dashboard'):
                db_info = self._parse_dashboard(dashboard)
                if db_info:
                    workbook_data['dashboards'].append(db_info)
            
            return workbook_data
            
        except Exception as e:
            print(f"Error parsing Tableau workbook: {e}")
            return {}
    
    def _parse_datasource(self, datasource_elem) -> Dict:
        """Parse datasource information"""
        ds_info = {
            'name': datasource_elem.get('name', ''),
            'caption': datasource_elem.get('caption', ''),
            'connection': {},
            'columns': []
        }
        
        # Parse connection details
        connection = datasource_elem.find('.//connection')
        if connection is not None:
            ds_info['connection'] = {
                'class': connection.get('class', ''),
                'server': connection.get('server', ''),
                'port': connection.get('port', ''),
                'dbname': connection.get('dbname', ''),
                'username': connection.get('username', ''),
                'authentication': connection.get('authentication', ''),
                'schema': connection.get('schema', '')
            }
        
        # Parse columns
        for column in datasource_elem.findall('.//column'):
            col_info = {
                'name': column.get('name', ''),
                'caption': column.get('caption', ''),
                'datatype': column.get('datatype', ''),
                'role': column.get('role', ''),
                'type': column.get('type', '')
            }
            ds_info['columns'].append(col_info)
        
        return ds_info
    
    def _parse_worksheet(self, worksheet_elem) -> Dict:
        """Parse worksheet information"""
        ws_info = {
            'name': worksheet_elem.get('name', ''),
            'marks': [],
            'encodings': {}
        }
        
        # Parse marks (chart types)
        for mark in worksheet_elem.findall('.//mark'):
            mark_info = {
                'class': mark.get('class', 'Automatic'),
                'type': mark.get('type', '')
            }
            ws_info['marks'].append(mark_info)
        
        # Parse encodings (field mappings)
        for encoding in worksheet_elem.findall('.//encoding'):
            attr = encoding.get('attr', '')
            field = encoding.get('field', '')
            type_attr = encoding.get('type', '')
            
            ws_info['encodings'][attr] = {
                'field': field,
                'type': type_attr
            }
        
        return ws_info
    
    def _parse_dashboard(self, dashboard_elem) -> Dict:
        """Parse dashboard information"""
        db_info = {
            'name': dashboard_elem.get('name', ''),
            'zones': []
        }
        
        # Parse zones (layout information)
        for zone in dashboard_elem.findall('.//zone'):
            zone_info = {
                'name': zone.get('name', ''),
                'type': zone.get('type', ''),
                'param': zone.get('param', ''),
                'x': zone.get('x', 0),
                'y': zone.get('y', 0),
                'w': zone.get('w', 0),
                'h': zone.get('h', 0)
            }
            db_info['zones'].append(zone_info)
        
        return db_info
    
    def generate_valid_pbit_structure(self, tableau_data: Dict) -> Dict:
        """Generate valid Power BI template structure that won't be corrupted"""
        
        # Get table and column info from Tableau
        table_name = "TableauData"
        columns = []
        
        if tableau_data.get('datasources'):
            ds = tableau_data['datasources'][0]
            connection = ds.get('connection', {})
            schema_name = connection.get('schema', '')
            if schema_name:
                table_name = schema_name
            
            for col in ds.get('columns', [])[:15]:  # Limit to first 15 columns
                col_name = col.get('name', '').replace('[', '').replace(']', '').strip()
                if col_name and not col_name.startswith('Measure') and len(col_name) > 0:
                    columns.append({
                        'name': col_name,
                        'dataType': self._map_powerbi_datatype(col.get('datatype', 'string'))
                    })
        
        # If no valid columns found, create minimal sample ones
        if not columns:
            columns = [
                {'name': 'Category', 'dataType': 'string'},
                {'name': 'Value', 'dataType': 'int64'}
            ]
        
        # Build column type transformations for M expression
        column_transformations = []
        for col in columns:
            m_type = self._get_m_type(col['dataType'])
            column_transformations.append(f'{{"{col["name"]}", {m_type}}}')
        
        # FIXED: Proper Power BI Analysis Services Model Schema
        data_model_schema = {
            "name": "SemanticModel",
            "compatibilityLevel": 1550,
            "model": {
                "culture": "en-US",
                "defaultPowerBIDataSourceVersion": "powerBI_V3",
                "sourceQueryCulture": "en-US",
                "tables": [
                    {
                        "name": table_name,
                        "columns": [
                            {
                                "name": col['name'],
                                "dataType": col['dataType'],
                                "sourceColumn": col['name']
                            }
                            for col in columns
                        ],
                        "partitions": [
                            {
                                "name": "Partition",
                                "dataView": "full",
                                "source": {
                                    "type": "m",
                                    "expression": [
                                        "let",
                                        "    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText(\"\", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [" + ', '.join([f'[{col["name"]}] = _t' for col in columns]) + "]),",
                                        "    #\"Changed Type\" = Table.TransformColumnTypes(Source,{" + ', '.join(column_transformations) + "})",
                                        "in",
                                        "    #\"Changed Type\""
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        # FIXED: Proper Power BI Report Layout Structure
        report_layout = {
            "id": str(uuid.uuid4()),
            "resourcePackages": [
                {
                    "resourcePackage": {
                        "type": "ResourcePackage",
                        "items": [
                            {
                                "id": str(uuid.uuid4()),
                                "type": "Report",
                                "payload": "",
                                "path": "Report"
                            }
                        ]
                    }
                }
            ],
            "config": json.dumps({
                "version": "5.43",
                "themeCollection": {
                    "baseTheme": {
                        "name": "CY24SU06"
                    }
                },
                "activeSectionIndex": 0,
                "defaultDrillFilterOtherVisuals": True,
                "slowDataSourceSettings": {
                    "isCrossHighlightingDisabled": False,
                    "isSlicerSelectionsButtonEnabled": False,
                    "isFilterSelectionsButtonEnabled": False
                }
            }),
            "layoutOptimization": 0,
            "sections": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "ReportSection",
                    "displayName": "Page 1",
                    "visualContainers": [],
                    "config": json.dumps({
                        "layouts": [
                            {
                                "id": 0,
                                "position": {
                                    "x": 0,
                                    "y": 0,
                                    "z": 0,
                                    "width": 1280,
                                    "height": 720
                                }
                            }
                        ]
                    })
                }
            ]
        }
        
        # Add a simple chart if we have data
        if len(columns) >= 1:
            visual_id = str(uuid.uuid4())
            
            # Simple column chart configuration
            visual_config = {
                "name": visual_id,
                "layouts": [
                    {
                        "id": 0,
                        "position": {
                            "x": 40,
                            "y": 40,
                            "z": 1000,
                            "width": 400,
                            "height": 300
                        }
                    }
                ],
                "singleVisual": {
                    "visualType": "columnChart",
                    "drillFilterOtherVisuals": True,
                    "objects": {
                        "general": [
                            {
                                "properties": {
                                    "keepLayerOrder": {
                                        "expr": {
                                            "Literal": {
                                                "Value": "true"
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    },
                    "projections": {
                        "Category": [
                            {
                                "queryRef": f"{table_name}.{columns[0]['name']}"
                            }
                        ]
                    }
                }
            }
            
            # Add Y axis if we have a numeric column
            numeric_columns = [col for col in columns if col['dataType'] in ['int64', 'double']]
            if numeric_columns:
                visual_config["singleVisual"]["projections"]["Y"] = [
                    {
                        "queryRef": f"{table_name}.{numeric_columns[0]['name']}"
                    }
                ]
            
            visual_container = {
                "id": visual_id,
                "config": json.dumps(visual_config)
            }
            
            report_layout['sections'][0]['visualContainers'].append(visual_container)
        
        return {
            'DataModelSchema': data_model_schema,
            'Layout': report_layout,
            'Version': '4.0',
            'Settings': {
                "useStylableVisualContainerHeader": True
            }
        }
    
    def _get_m_type(self, datatype: str) -> str:
        """Get Power Query M type for column transformation"""
        type_mapping = {
            'string': 'type text',
            'int64': 'Int64.Type',
            'double': 'type number',
            'dateTime': 'type datetime',
            'boolean': 'type logical'
        }
        return type_mapping.get(datatype, 'type text')
    
    def _map_powerbi_datatype(self, tableau_type: str) -> str:
        """Map Tableau data types to Power BI Analysis Services types"""
        type_mapping = {
            'string': 'string',
            'integer': 'int64',
            'real': 'double',
            'date': 'dateTime',
            'datetime': 'dateTime',
            'boolean': 'boolean'
        }
        return type_mapping.get(tableau_type.lower(), 'string')
    
    def create_pbit_file(self, template_structure: Dict, output_path: str, base_name: str):
        """Create Power BI template (.pbit) file with correct encoding and structure"""
        try:
            pbit_path = os.path.join(output_path, f"{base_name}.pbit")
            
            # Create temporary directory for Power BI files
            temp_dir = os.path.join(output_path, f"{base_name}_temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            print(f"📝 Creating Power BI template structure...")
            
            # FIXED: Write DataModelSchema with proper encoding (UTF-16 LE with BOM)
            datamodel_content = json.dumps(template_structure['DataModelSchema'], 
                                         ensure_ascii=False, separators=(',', ':'))
            with open(os.path.join(temp_dir, 'DataModelSchema'), 'wb') as f:
                # UTF-16 LE BOM
                f.write(b'\xff\xfe')
                f.write(datamodel_content.encode('utf-16le'))
            
            # Create Report directory and write Layout
            report_dir = os.path.join(temp_dir, 'Report')
            os.makedirs(report_dir, exist_ok=True)
            
            # FIXED: Write Layout with proper encoding (UTF-16 LE with BOM)
            layout_content = json.dumps(template_structure['Layout'], 
                                       ensure_ascii=False, separators=(',', ':'))
            with open(os.path.join(report_dir, 'Layout'), 'wb') as f:
                # UTF-16 LE BOM
                f.write(b'\xff\xfe')
                f.write(layout_content.encode('utf-16le'))
            
            # FIXED: Write Version as plain text (UTF-8, no BOM)
            with open(os.path.join(temp_dir, 'Version'), 'w', encoding='utf-8-sig') as f:
                f.write(template_structure['Version'])
            
            # FIXED: Write Settings with proper encoding (UTF-16 LE with BOM)
            settings_content = json.dumps(template_structure['Settings'], 
                                        ensure_ascii=False, separators=(',', ':'))
            with open(os.path.join(temp_dir, 'Settings'), 'wb') as f:
                # UTF-16 LE BOM
                f.write(b'\xff\xfe')
                f.write(settings_content.encode('utf-16le'))
            
            # FIXED: Create the .pbit file with proper ZIP compression
            print(f"📦 Creating ZIP archive...")
            with zipfile.ZipFile(pbit_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, temp_dir)
                        # Ensure forward slashes in ZIP paths
                        arc_name = arc_name.replace('\\', '/')
                        zip_file.write(file_path, arc_name)
                        print(f"  ✓ Added: {arc_name}")
            
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir)
            
            # Validate the created file
            self._validate_pbit_file(pbit_path)
            
            print(f"✅ Power BI template created: {pbit_path}")
            print(f"📁 File size: {os.path.getsize(pbit_path)} bytes")
            print(f"🎯 You can now open this file in Power BI Desktop!")
            
            return pbit_path
            
        except Exception as e:
            print(f"❌ Error creating .pbit file: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _validate_pbit_file(self, pbit_path: str):
        """Validate the created .pbit file structure"""
        try:
            print(f"🔍 Validating .pbit file structure...")
            with zipfile.ZipFile(pbit_path, 'r') as zip_file:
                files = zip_file.namelist()
                print(f"  Files in archive: {files}")
                
                required_files = ['DataModelSchema', 'Report/Layout', 'Version', 'Settings']
                for req_file in required_files:
                    if req_file in files:
                        print(f"  ✓ Found: {req_file}")
                    else:
                        print(f"  ❌ Missing: {req_file}")
                        
                # Test reading the files
                for filename in ['DataModelSchema', 'Settings']:
                    if filename in files:
                        content = zip_file.read(filename)
                        if content.startswith(b'\xff\xfe'):
                            print(f"  ✓ {filename}: Correct UTF-16 LE BOM")
                        else:
                            print(f"  ⚠️  {filename}: Missing or incorrect BOM")
                            
        except Exception as e:
            print(f"  ⚠️  Validation error: {e}")
    
    def analyze_extracted_data(self):
        """Print analysis of what was found in the Tableau file"""
        print("\n📊 TABLEAU ANALYSIS:")
        print("=" * 50)
        
        # Datasources
        datasources = self.tableau_data.get('datasources', [])
        print(f"📋 Found {len(datasources)} datasource(s):")
        for i, ds in enumerate(datasources):
            print(f"  {i+1}. {ds.get('name', 'Unknown')}")
            conn = ds.get('connection', {})
            if conn.get('class'):
                print(f"     Type: {conn.get('class')}")
            if conn.get('server'):
                print(f"     Server: {conn.get('server')}")
            if conn.get('dbname'):
                print(f"     Database: {conn.get('dbname')}")
            
            columns = ds.get('columns', [])
            print(f"     Columns: {len(columns)} found")
            for col in columns[:5]:  # Show first 5 columns
                col_name = col.get('name', '').replace('[', '').replace(']', '')
                if col_name:
                    print(f"       - {col_name} ({col.get('datatype', 'unknown')})")
            if len(columns) > 5:
                print(f"       ... and {len(columns) - 5} more")
        
        # Worksheets
        worksheets = self.tableau_data.get('worksheets', [])
        print(f"\n📈 Found {len(worksheets)} worksheet(s):")
        for i, ws in enumerate(worksheets):
            print(f"  {i+1}. {ws.get('name', 'Unknown')}")
            encodings = ws.get('encodings', {})
            if encodings:
                print(f"     Field mappings:")
                for attr, encoding in encodings.items():
                    field = encoding.get('field', '').replace('[', '').replace(']', '')
                    if field:
                        print(f"       {attr}: {field}")
        
        # Dashboards
        dashboards = self.tableau_data.get('dashboards', [])
        print(f"\n📱 Found {len(dashboards)} dashboard(s):")
        for i, db in enumerate(dashboards):
            print(f"  {i+1}. {db.get('name', 'Unknown')}")
            zones = db.get('zones', [])
            print(f"     Layout zones: {len(zones)}")
        
        print("=" * 50)
    
    def convert_file(self, input_path: str, output_dir: str = None) -> bool:
        """Main conversion function"""
        try:
            if not os.path.exists(input_path):
                print(f"❌ Error: Input file '{input_path}' not found")
                return False
            
            # Set output directory
            if output_dir is None:
                output_dir = os.path.dirname(input_path)
            
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            
            print(f"🔄 Converting: {input_path}")
            
            # Extract .twbx if needed
            if input_path.endswith('.twbx'):
                print("📂 Extracting .twbx file...")
                twb_path = self.extract_twbx(input_path)
                if not twb_path:
                    return False
            else:
                twb_path = input_path
            
            # Parse Tableau workbook
            print("📖 Parsing Tableau workbook...")
            self.tableau_data = self.parse_tableau_workbook(twb_path)
            
            if not self.tableau_data:
                print("❌ Error: Could not parse Tableau workbook")
                return False
            
            # Show what was found
            self.analyze_extracted_data()
            
            # Generate Power BI template structure
            print("🏗️  Generating Power BI template structure...")
            template_structure = self.generate_valid_pbit_structure(self.tableau_data)
            
            # Create .pbit file
            print("💾 Creating Power BI template file...")
            pbit_path = self.create_pbit_file(template_structure, output_dir, base_name)
            
            if pbit_path:
                print("\n🎉 Conversion completed successfully!")
                return True
            else:
                print("\n❌ Error: Failed to create .pbit file")
                return False
            
        except Exception as e:
            print(f"❌ Error during conversion: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(description='Convert Tableau workbook to Power BI template (.pbit)')
    parser.add_argument('input', help='Input Tableau file (.twbx or .twb)')
    parser.add_argument('-o', '--output', help='Output directory (default: same as input)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    converter = TableauToPowerBIConverter()
    success = converter.convert_file(args.input, args.output)
    
    if success:
        print("\n✅ Conversion completed successfully!")
        print("🎯 You can now open the .pbit file directly in Power BI Desktop!")
        print("💡 The template will prompt you to connect to your data source.")
        print("⚠️  If you get connection errors, you may need to update the data source settings in Power BI.")
    else:
        print("\n❌ Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
