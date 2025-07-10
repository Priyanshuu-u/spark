#!/usr/bin/env python3
"""
Tableau to Power BI Converter
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
    
    def convert_to_powerbi(self, tableau_data: Dict) -> Dict:
        """Convert Tableau data to Power BI format"""
        powerbi_config = {
            'version': '1.0',
            'config': {
                'name': tableau_data.get('name', 'Converted Dashboard'),
                'pages': [],
                'dataSources': [],
                'measures': [],
                'relationships': []
            }
        }
        
        # Convert datasources
        for ds in tableau_data.get('datasources', []):
            pbi_datasource = self._convert_datasource(ds)
            if pbi_datasource:
                powerbi_config['config']['dataSources'].append(pbi_datasource)
        
        # Convert worksheets to pages
        for ws in tableau_data.get('worksheets', []):
            pbi_page = self._convert_worksheet(ws, tableau_data.get('datasources', []))
            if pbi_page:
                powerbi_config['config']['pages'].append(pbi_page)
        
        return powerbi_config
    
    def _convert_datasource(self, tableau_ds: Dict) -> Dict:
        """Convert Tableau datasource to Power BI format"""
        connection = tableau_ds.get('connection', {})
        
        # Map Tableau connection types to Power BI
        connection_mapping = {
            'oracle': 'Oracle',
            'sqlserver': 'SqlServer',
            'mysql': 'MySql',
            'postgresql': 'PostgreSQL'
        }
        
        conn_class = connection.get('class', '').lower()
        pbi_connection_type = connection_mapping.get(conn_class, 'Generic')
        
        pbi_datasource = {
            'name': tableau_ds.get('name', ''),
            'connectionType': pbi_connection_type,
            'connectionString': self._build_connection_string(connection),
            'tables': []
        }
        
        # Convert columns to table schema
        table_name = connection.get('schema', 'default_table')
        columns = []
        
        for col in tableau_ds.get('columns', []):
            col_name = col.get('name', '').replace('[', '').replace(']', '')
            if col_name and not col_name.startswith('Measure'):
                columns.append({
                    'name': col_name,
                    'type': self._map_datatype(col.get('datatype', 'string')),
                    'role': col.get('role', 'dimension')
                })
        
        if columns:
            pbi_datasource['tables'].append({
                'name': table_name,
                'columns': columns
            })
        
        return pbi_datasource
    
    def _convert_worksheet(self, tableau_ws: Dict, datasources: List[Dict]) -> Dict:
        """Convert Tableau worksheet to Power BI page"""
        pbi_page = {
            'name': tableau_ws.get('name', ''),
            'visualizations': []
        }
        
        # Determine chart type
        chart_type = 'clusteredBarChart'  # Default for your use case
        marks = tableau_ws.get('marks', [])
        if marks:
            mark_class = marks[0].get('class', 'Automatic').lower()
            if 'bar' in mark_class:
                chart_type = 'clusteredBarChart'
            elif 'line' in mark_class:
                chart_type = 'lineChart'
            elif 'area' in mark_class:
                chart_type = 'areaChart'
        
        # Parse encodings to determine fields
        encodings = tableau_ws.get('encodings', {})
        
        # Map Tableau shelf positions to Power BI roles
        category_field = None
        value_field = None
        
        for attr, encoding in encodings.items():
            field = encoding.get('field', '').replace('[', '').replace(']', '')
            if attr in ['x', 'columns'] and field:
                category_field = field
            elif attr in ['y', 'rows'] and field:
                value_field = field
        
        # Create visualization
        if category_field and value_field:
            visualization = {
                'type': chart_type,
                'title': f"{category_field} vs {value_field}",
                'position': {
                    'x': 0,
                    'y': 0,
                    'width': 600,
                    'height': 400
                },
                'dataRoles': {
                    'category': [category_field],
                    'values': [value_field]
                },
                'formatting': {
                    'title': {
                        'show': True,
                        'text': f"{category_field} Analysis"
                    },
                    'categoryAxis': {
                        'show': True,
                        'title': category_field
                    },
                    'valueAxis': {
                        'show': True,
                        'title': value_field
                    }
                }
            }
            
            pbi_page['visualizations'].append(visualization)
        
        return pbi_page
    
    def _build_connection_string(self, connection: Dict) -> str:
        """Build connection string for Power BI"""
        conn_class = connection.get('class', '').lower()
        server = connection.get('server', 'localhost')
        port = connection.get('port', '')
        dbname = connection.get('dbname', '')
        schema = connection.get('schema', '')
        
        if conn_class == 'oracle':
            port_str = f":{port}" if port else ":1521"
            return f"Data Source={server}{port_str};Initial Catalog={dbname};Provider=OraOLEDB.Oracle;"
        elif conn_class == 'sqlserver':
            return f"Data Source={server};Initial Catalog={dbname};Integrated Security=True;"
        elif conn_class == 'mysql':
            port_str = f";Port={port}" if port else ";Port=3306"
            return f"Server={server};Database={dbname}{port_str};Uid=username;Pwd=password;"
        else:
            return f"Data Source={server};Initial Catalog={dbname};"
    
    def _map_datatype(self, tableau_type: str) -> str:
        """Map Tableau data types to Power BI types"""
        type_mapping = {
            'string': 'Text',
            'integer': 'Whole Number',
            'real': 'Decimal Number',
            'date': 'Date',
            'datetime': 'Date/Time',
            'boolean': 'True/False'
        }
        return type_mapping.get(tableau_type.lower(), 'Text')
    
    def generate_powerbi_template_structure(self, tableau_data: Dict) -> Dict:
        """Generate Power BI template structure"""
        # Generate unique IDs for Power BI objects
        report_id = str(uuid.uuid4())
        page_id = str(uuid.uuid4())
        
        # Create data model schema
        data_model_schema = {
            "name": "SemanticModel",
            "compatibilityLevel": 1567,
            "model": {
                "culture": "en-US",
                "dataSources": [],
                "tables": [],
                "relationships": [],
                "roles": [],
                "measures": []
            }
        }
        
        # Add data sources from Tableau
        for ds in tableau_data.get('datasources', []):
            connection = ds.get('connection', {})
            data_source = {
                "type": "structured",
                "name": ds.get('name', 'DataSource'),
                "connectionDetails": {
                    "protocol": self._get_powerbi_protocol(connection.get('class', '')),
                    "address": {
                        "server": connection.get('server', 'localhost'),
                        "database": connection.get('dbname', '')
                    }
                }
            }
            data_model_schema['model']['dataSources'].append(data_source)
            
            # Add table
            table_name = connection.get('schema', 'Table1')
            table = {
                "name": table_name,
                "columns": []
            }
            
            for col in ds.get('columns', []):
                col_name = col.get('name', '').replace('[', '').replace(']', '')
                if col_name and not col_name.startswith('Measure'):
                    column = {
                        "name": col_name,
                        "dataType": self._map_powerbi_datatype(col.get('datatype', 'string')),
                        "sourceColumn": col_name
                    }
                    table['columns'].append(column)
            
            data_model_schema['model']['tables'].append(table)
        
        # Create report layout
        report_layout = {
            "id": report_id,
            "resourcePackages": [],
            "sections": [
                {
                    "id": page_id,
                    "name": "Page1",
                    "filters": [],
                    "objects": {
                        "section": [
                            {
                                "properties": {
                                    "verticalAlignment": {
                                        "expr": {
                                            "Literal": {
                                                "Value": "'Top'"
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    },
                    "visualContainers": []
                }
            ]
        }
        
        # Add visualizations
        visual_counter = 0
        for ws in tableau_data.get('worksheets', []):
            visual_id = str(uuid.uuid4())
            visual_counter += 1
            
            # Get chart type and fields
            encodings = ws.get('encodings', {})
            category_field = None
            value_field = None
            
            for attr, encoding in encodings.items():
                field = encoding.get('field', '').replace('[', '').replace(']', '')
                if attr in ['x', 'columns'] and field:
                    category_field = field
                elif attr in ['y', 'rows'] and field:
                    value_field = field
            
            if category_field and value_field:
                # Determine table name
                table_name = 'Table1'
                if tableau_data.get('datasources'):
                    table_name = tableau_data['datasources'][0].get('connection', {}).get('schema', 'Table1')
                
                visual_container = {
                    "id": visual_id,
                    "height": 300,
                    "width": 400,
                    "x": 50 + (visual_counter - 1) * 420,
                    "y": 50,
                    "z": visual_counter,
                    "config": json.dumps({
                        "name": f"visual_{visual_counter}",
                        "layouts": [
                            {
                                "id": 0,
                                "position": {
                                    "x": 50 + (visual_counter - 1) * 420,
                                    "y": 50,
                                    "z": visual_counter,
                                    "width": 400,
                                    "height": 300
                                }
                            }
                        ],
                        "singleVisual": {
                            "visualType": "clusteredBarChart",
                            "projections": {
                                "Category": [
                                    {
                                        "queryRef": f"{table_name}.{category_field}"
                                    }
                                ],
                                "Y": [
                                    {
                                        "queryRef": f"{table_name}.{value_field}"
                                    }
                                ]
                            },
                            "prototypeQuery": {
                                "Version": 2,
                                "From": [
                                    {
                                        "Name": table_name[0].upper(),
                                        "Entity": table_name,
                                        "Type": 0
                                    }
                                ],
                                "Select": [
                                    {
                                        "Column": {
                                            "Expression": {
                                                "SourceRef": {
                                                    "Source": table_name[0].upper()
                                                }
                                            },
                                            "Property": category_field
                                        },
                                        "Name": f"{table_name}.{category_field}"
                                    },
                                    {
                                        "Aggregation": {
                                            "Expression": {
                                                "Column": {
                                                    "Expression": {
                                                        "SourceRef": {
                                                            "Source": table_name[0].upper()
                                                        }
                                                    },
                                                    "Property": value_field
                                                }
                                            },
                                            "Function": 5
                                        },
                                        "Name": f"Sum({table_name}.{value_field})"
                                    }
                                ]
                            }
                        }
                    })
                }
                
                report_layout['sections'][0]['visualContainers'].append(visual_container)
        
        return {
            'DataModelSchema': data_model_schema,
            'ReportLayout': report_layout,
            'Version': '1.0',
            'Settings': {
                "useStylableVisualContainerHeader": True
            }
        }
    
    def _get_powerbi_protocol(self, tableau_class: str) -> str:
        """Map Tableau connection class to Power BI protocol"""
        mapping = {
            'oracle': 'oracle',
            'sqlserver': 'tds',
            'mysql': 'mysql',
            'postgresql': 'postgresql'
        }
        return mapping.get(tableau_class.lower(), 'generic')
    
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
        """Create Power BI template (.pbit) file"""
        try:
            pbit_path = os.path.join(output_path, f"{base_name}.pbit")
            
            # Create temporary directory for Power BI files
            temp_dir = os.path.join(output_path, f"{base_name}_temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Write DataModelSchema
            with open(os.path.join(temp_dir, 'DataModelSchema'), 'w', encoding='utf-16-le') as f:
                f.write('\ufeff')  # BOM for UTF-16 LE
                json.dump(template_structure['DataModelSchema'], f, ensure_ascii=False, separators=(',', ':'))
            
            # Write Layout
            layout_dir = os.path.join(temp_dir, 'Report')
            os.makedirs(layout_dir, exist_ok=True)
            with open(os.path.join(layout_dir, 'Layout'), 'w', encoding='utf-16-le') as f:
                f.write('\ufeff')  # BOM for UTF-16 LE
                json.dump(template_structure['ReportLayout'], f, ensure_ascii=False, separators=(',', ':'))
            
            # Write Version
            with open(os.path.join(temp_dir, 'Version'), 'w', encoding='utf-8') as f:
                f.write(template_structure['Version'])
            
            # Write Settings
            with open(os.path.join(temp_dir, 'Settings'), 'w', encoding='utf-16-le') as f:
                f.write('\ufeff')  # BOM for UTF-16 LE
                json.dump(template_structure['Settings'], f, ensure_ascii=False, separators=(',', ':'))
            
            # Create the .pbit file (ZIP archive)
            with zipfile.ZipFile(pbit_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, arc_name)
            
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir)
            
            print(f"✅ Power BI template created: {pbit_path}")
            print(f"📁 You can now open this file directly in Power BI Desktop!")
            
            return pbit_path
            
        except Exception as e:
            print(f"Error creating .pbit file: {e}")
            return None
    
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
                print(f"Error: Input file '{input_path}' not found")
                return False
            
            # Set output directory
            if output_dir is None:
                output_dir = os.path.dirname(input_path)
            
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            
            print(f"Converting: {input_path}")
            
            # Extract .twbx if needed
            if input_path.endswith('.twbx'):
                twb_path = self.extract_twbx(input_path)
                if not twb_path:
                    return False
            else:
                twb_path = input_path
            
            # Parse Tableau workbook
            print("Parsing Tableau workbook...")
            self.tableau_data = self.parse_tableau_workbook(twb_path)
            
            if not self.tableau_data:
                print("Error: Could not parse Tableau workbook")
                return False
            
            # Show what was found
            self.analyze_extracted_data()
            
            # Generate Power BI template structure
            print("Generating Power BI template structure...")
            template_structure = self.generate_powerbi_template_structure(self.tableau_data)
            
            # Create .pbit file
            print("Creating Power BI template file...")
            pbit_path = self.create_pbit_file(template_structure, output_dir, base_name)
            
            if pbit_path:
                print("Conversion completed successfully!")
                return True
            else:
                print("Error: Failed to create .pbit file")
                return False
            
        except Exception as e:
            print(f"Error during conversion: {e}")
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
    else:
        print("\n❌ Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
