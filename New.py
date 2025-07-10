#!/usr/bin/env python3
"""
Tableau to Power BI Converter
Converts Tableau .twbx files to Power BI compatible format
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
    
    def _generate_setup_instructions(self, powerbi_config: Dict) -> str:
        """Generate setup instructions for Power BI"""
        instructions = """# Power BI Setup Instructions

## Generated from Tableau Workbook

### Step 1: Data Source Connection
1. Open Power BI Desktop
2. Click "Get Data" → "More..."
3. Select your database type (Oracle/SQL Server/etc.)
4. Use the connection details from the configuration file

### Step 2: Import Data
1. Select the required tables
2. Transform data if needed using Power Query Editor
3. Load the data into Power BI

### Step 3: Create Measures
1. Go to the "Modeling" tab
2. Click "New Measure"
3. Copy and paste the DAX formulas from the measures file

### Step 4: Create Visualizations
1. Add a new visual to your report
2. Configure the fields according to the JSON configuration
3. Apply formatting as specified

### Step 5: Dashboard Layout
1. Arrange visuals according to the position specifications
2. Add titles and formatting
3. Save your Power BI file

## Configuration Details
"""
        
        # Add datasource details
        for ds in powerbi_config.get('config', {}).get('dataSources', []):
            instructions += f"""
### Data Source: {ds.get('name', 'Unknown')}
- Connection Type: {ds.get('connectionType', 'Unknown')}
- Connection String: {ds.get('connectionString', 'Not specified')}
"""
        
        return instructions
    
    def save_powerbi_files(self, powerbi_config: Dict, output_dir: str, base_name: str):
        """Save Power BI configuration files"""
        try:
            # Clean up the output directory path
            output_dir = os.path.abspath(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            
            # Clean up base name - remove invalid characters
            base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
            
            # Save JSON configuration
            json_path = os.path.join(output_dir, f"{base_name}_powerbi_config.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(powerbi_config, f, indent=2, ensure_ascii=False)
        
            # Save DAX measures
            try:
                measures = self.generate_dax_measures(self.tableau_data)
                dax_path = os.path.join(output_dir, f"{base_name}_measures.dax")
                with open(dax_path, 'w', encoding='utf-8') as f:
                    f.write("// DAX Measures for Power BI\n")
                    f.write("// Generated from Tableau workbook\n\n")
                    
                    for measure in measures:
                        f.write(f"// {measure['name']}\n")
                        f.write(f"{measure['name']} = {measure['expression']}\n\n")
                
                # Save setup instructions
                instructions_path = os.path.join(output_dir, f"{base_name}_setup_instructions.md")
                with open(instructions_path, 'w', encoding='utf-8') as f:
                    f.write(self._generate_setup_instructions(powerbi_config))
                
                print(f"Files saved to: {output_dir}")
                print(f"- Configuration: {json_path}")
                print(f"- DAX Measures: {dax_path}")
                print(f"- Instructions: {instructions_path}")
                
            except Exception as e:
                print(f"Warning: Could not save some files: {e}")
                print(f"Main configuration saved to: {json_path}")
                
        except Exception as e:
            print(f"Error saving files: {e}")
            # At least try to save the main config file to desktop
            try:
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                fallback_path = os.path.join(desktop_path, f"{base_name}_powerbi_config.json")
                with open(fallback_path, 'w', encoding='utf-8') as f:
                    json.dump(powerbi_config, f, indent=2, ensure_ascii=False)
                print(f"Configuration saved to desktop: {fallback_path}")
            except:
                print("Could not save files. Please check permissions and paths.")
    
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
            
            # Save output files
            print("Saving Power BI files...")
            self.save_powerbi_files(powerbi_config, output_dir, base_name)
            
            print("Conversion completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error during conversion: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Convert Tableau workbook to Power BI format')
    parser.add_argument('input', help='Input Tableau file (.twbx or .twb)')
    parser.add_argument('-o', '--output', help='Output directory (default: same as input)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    converter = TableauToPowerBIConverter()
    success = converter.convert_file(args.input, args.output)
    
    if success:
        print("\n✅ Conversion completed successfully!")
        print("Check the output directory for:")
        print("- PowerBI configuration JSON")
        print("- DAX measures file")
        print("- Setup instructions")
    else:
        print("\n❌ Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
