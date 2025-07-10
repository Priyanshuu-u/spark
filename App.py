#!/usr/bin/env python3
"""
Tableau to Power BI Converter
Converts Tableau .twbx files to Power BI template (.pbit) files
Specifically handles bar charts with Oracle database connections
"""

import zipfile
import xml.etree.ElementTree as ET
import json
import os
import sys
from pathlib import Path
import argparse
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime

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
    
    def generate_dax_measures(self, tableau_data: Dict) -> List[Dict]:
        """Generate DAX measures from Tableau calculated fields"""
        measures = []
        
        # Generate common measures for your use case
        for ds in tableau_data.get('datasources', []):
            table_name = ds.get('connection', {}).get('schema', 'Table')
            
            # Find numeric columns for aggregation
            for col in ds.get('columns', []):
                col_name = col.get('name', '').replace('[', '').replace(']', '')
                if col.get('datatype', '') in ['integer', 'real'] and col_name:
                    measures.append({
                        'name': f'Total {col_name}',
                        'expression': f'SUM({table_name}[{col_name}])',
                        'formatString': '#,##0'
                    })
                    
                    measures.append({
                        'name': f'Average {col_name}',
                        'expression': f'AVERAGE({table_name}[{col_name}])',
                        'formatString': '#,##0.00'
                    })
        
        return measures
    
    def generate_powerbi_template(self, powerbi_config: Dict, output_dir: str, base_name: str):
        """Generate actual Power BI template (.pbit) file"""
        try:
            # Clean up the output directory path
            output_dir = os.path.abspath(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            
            # Clean up base name - remove invalid characters
            base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
            
            # Create .pbit file path
            pbit_path = os.path.join(output_dir, f"{base_name}.pbit")
            
            # Generate Power BI template structure
            template_files = self._generate_pbit_structure(powerbi_config)
            
            # Create ZIP file (.pbit is essentially a ZIP file)
            with zipfile.ZipFile(pbit_path, 'w', zipfile.ZIP_DEFLATED) as pbit_file:
                for file_path, content in template_files.items():
                    pbit_file.writestr(file_path, content)
            
            print(f"✅ Power BI template created: {pbit_path}")
            print(f"📁 Template can be opened directly in Power BI Desktop")
            return True
            
        except Exception as e:
            print(f"❌ Error creating Power BI template: {e}")
            return False
    
    def _generate_pbit_structure(self, powerbi_config: Dict) -> Dict[str, str]:
        """Generate the internal structure of .pbit file"""
        files = {}
        
        # Generate DataModelSchema
        files["DataModelSchema"] = self._generate_data_model_schema(powerbi_config)
        
        # Generate DiagramLayout
        files["DiagramLayout"] = self._generate_diagram_layout(powerbi_config)
        
        # Generate Report/Layout
        files["Report/Layout"] = self._generate_report_layout(powerbi_config)
        
        # Generate Settings
        files["Settings"] = self._generate_settings()
        
        # Generate Version
        files["Version"] = self._generate_version()
        
        return files
    
    def _generate_data_model_schema(self, powerbi_config: Dict) -> str:
        """Generate DataModelSchema JSON for Power BI"""
        data_sources = powerbi_config.get('config', {}).get('dataSources', [])
        
        # Generate tables from data sources
        tables = []
        for i, ds in enumerate(data_sources):
            table_name = ds.get('name', f'Table{i+1}')
            columns = []
            
            # Add columns from the datasource
            for table in ds.get('tables', []):
                for col in table.get('columns', []):
                    columns.append({
                        "name": col.get('name', 'Column'),
                        "dataType": self._map_powerbi_datatype(col.get('type', 'Text')),
                        "sourceColumn": col.get('name', 'Column'),
                        "summarizeBy": "none" if col.get('role') == 'dimension' else "sum"
                    })
            
            # Generate basic table structure
            table_def = {
                "name": table_name,
                "columns": columns,
                "partitions": [
                    {
                        "name": f"Partition",
                        "dataView": "full",
                        "source": {
                            "type": "m",
                            "expression": self._generate_m_query(ds)
                        }
                    }
                ]
            }
            tables.append(table_def)
        
        # Generate relationships (basic example)
        relationships = []
        
        # Generate measures
        measures = []
        tableau_data = getattr(self, 'tableau_data', {})
        dax_measures = self.generate_dax_measures(tableau_data)
        for measure in dax_measures:
            measures.append({
                "name": measure.get('name', 'Measure'),
                "expression": measure.get('expression', 'SUM(Table[Column])'),
                "formatString": measure.get('formatString', '#,##0'),
                "table": tables[0]["name"] if tables else "Table1"
            })
        
        schema = {
            "name": "SemanticModel",
            "compatibilityLevel": 1567,
            "model": {
                "culture": "en-US",
                "dataSources": [
                    {
                        "type": "structured",
                        "name": "localhost",
                        "connectionDetails": {
                            "protocol": "tds",
                            "address": {
                                "server": "localhost",
                                "database": "database"
                            }
                        },
                        "credential": {
                            "AuthenticationKind": "ServiceAccount",
                            "EncryptConnection": False
                        }
                    }
                ],
                "tables": tables,
                "relationships": relationships,
                "measures": measures,
                "annotations": [
                    {
                        "name": "ClientCompatibilityLevel",
                        "value": "600"
                    }
                ]
            }
        }
        
        return json.dumps(schema, indent=2)
    
    def _generate_diagram_layout(self, powerbi_config: Dict) -> str:
        """Generate DiagramLayout JSON for Power BI"""
        layout = {
            "version": 1,
            "objects": {}
        }
        return json.dumps(layout, indent=2)
    
    def _generate_report_layout(self, powerbi_config: Dict) -> str:
        """Generate Report/Layout JSON with visualizations for Power BI"""
        pages = powerbi_config.get('config', {}).get('pages', [])
        
        report_pages = []
        for i, page in enumerate(pages):
            page_id = str(uuid.uuid4())
            page_visuals = []
            
            # Convert visualizations
            for j, viz in enumerate(page.get('visualizations', [])):
                visual_id = str(uuid.uuid4())
                visual_config = self._convert_visualization_to_powerbi(viz, visual_id)
                page_visuals.append(visual_config)
            
            page_config = {
                "id": page_id,
                "name": page.get('name', f'Page {i+1}'),
                "displayName": page.get('name', f'Page {i+1}'),
                "visualContainers": page_visuals,
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
            report_pages.append(page_config)
        
        # If no pages exist, create a default page
        if not report_pages:
            report_pages.append({
                "id": str(uuid.uuid4()),
                "name": "Page 1",
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
            })
        
        report = {
            "id": str(uuid.uuid4()),
            "resourcePackages": [
                {
                    "resourcePackage": "Microsoft.AnalysisServices.Modeler.Common.UIPlaceholder",
                    "version": "13.0.0.0"
                }
            ],
            "pages": report_pages,
            "filters": "[]",
            "config": json.dumps({
                "version": "3.0",
                "themeCollection": {
                    "baseTheme": {
                        "name": "CityPark"
                    }
                }
            })
        }
        
        return json.dumps(report, indent=2)
    
    def _convert_visualization_to_powerbi(self, viz: Dict, visual_id: str) -> Dict:
        """Convert Tableau visualization to Power BI visual format"""
        viz_type = viz.get('type', 'clusteredBarChart')
        
        # Map Tableau chart types to Power BI visual types
        visual_type_mapping = {
            'clusteredBarChart': 'clusteredBarChart',
            'lineChart': 'lineChart',
            'areaChart': 'areaChart',
            'pieChart': 'pieChart',
            'scatterChart': 'scatterChart'
        }
        
        powerbi_visual_type = visual_type_mapping.get(viz_type, 'clusteredBarChart')
        
        # Generate basic visual configuration
        visual_config = {
            "id": visual_id,
            "position": {
                "x": viz.get('position', {}).get('x', 0),
                "y": viz.get('position', {}).get('y', 0),
                "z": 1000,
                "width": viz.get('position', {}).get('width', 300),
                "height": viz.get('position', {}).get('height', 200)
            },
            "config": json.dumps({
                "name": visual_id,
                "layouts": [
                    {
                        "id": 0,
                        "position": {
                            "x": viz.get('position', {}).get('x', 0),
                            "y": viz.get('position', {}).get('y', 0),
                            "z": 1000,
                            "width": viz.get('position', {}).get('width', 300),
                            "height": viz.get('position', {}).get('height', 200)
                        }
                    }
                ],
                "singleVisual": {
                    "visualType": powerbi_visual_type,
                    "objects": {},
                    "dataRoles": self._generate_data_roles(viz),
                    "vcObjects": {}
                }
            })
        }
        
        return visual_config
    
    def _generate_data_roles(self, viz: Dict) -> Dict:
        """Generate data roles for Power BI visual"""
        data_roles = viz.get('dataRoles', {})
        
        # Convert to Power BI format
        powerbi_roles = {}
        for role, fields in data_roles.items():
            if isinstance(fields, list):
                powerbi_roles[role] = [
                    {
                        "queryRef": f"Table.{field}",
                        "active": True
                    } for field in fields
                ]
        
        return powerbi_roles
    
    def _generate_m_query(self, datasource: Dict) -> str:
        """Generate M query for Power BI data source"""
        connection = datasource.get('connection', {})
        
        # Basic M query template
        if connection.get('connectionType') == 'Oracle':
            server = connection.get('connectionString', '').split(';')[0].replace('Data Source=', '')
            query = f'''let
    Source = Oracle.Database("{server}", [Query="SELECT * FROM SCHEMA.TABLE"])
in
    Source'''
        else:
            query = '''let
    Source = Table.FromRows({{"Column1", "Column2"}}, {{"Value1", "Value2"}})
in
    Source'''
        
        return query
    
    def _generate_settings(self) -> str:
        """Generate Settings JSON for Power BI"""
        settings = {
            "version": "1.0",
            "settings": {
                "useNewFilterPaneExperience": True,
                "allowChangeFilterTypes": True,
                "allowInlineHierarchyLabels": True,
                "fontSize": 8,
                "useEnhancedTooltips": True
            }
        }
        return json.dumps(settings, indent=2)
    
    def _generate_version(self) -> str:
        """Generate Version information for Power BI"""
        return "3.0"
    
    def _map_powerbi_datatype(self, tableau_type: str) -> str:
        """Map Tableau data types to Power BI data types"""
        type_mapping = {
            'Text': 'string',
            'Whole Number': 'int64',
            'Decimal Number': 'double',
            'Date': 'dateTime',
            'Date/Time': 'dateTime',
            'True/False': 'boolean'
        }
        return type_mapping.get(tableau_type, 'string')
    
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
            
            # Convert to Power BI format
            print("Converting to Power BI format...")
            powerbi_config = self.convert_to_powerbi(self.tableau_data)
            
            # Generate Power BI template (.pbit file)
            print("Generating Power BI template...")
            success = self.generate_powerbi_template(powerbi_config, output_dir, base_name)
            
            if success:
                print("✅ Conversion completed successfully!")
                print(f"📁 Power BI template (.pbit) ready for use!")
            else:
                print("⚠️  Conversion completed with warnings")
            
            return success
            
        except Exception as e:
            print(f"Error during conversion: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Convert Tableau workbook to Power BI template (.pbit) file')
    parser.add_argument('input', help='Input Tableau file (.twbx or .twb)')
    parser.add_argument('-o', '--output', help='Output directory (default: same as input)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    converter = TableauToPowerBIConverter()
    success = converter.convert_file(args.input, args.output)
    
    if success:
        print("\n✅ Conversion completed successfully!")
        print("🎯 Power BI template (.pbit) file generated!")
        print("📖 You can now open the .pbit file directly in Power BI Desktop")
    else:
        print("\n❌ Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
