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
    
    def generate_minimal_pbit_structure(self, tableau_data: Dict) -> Dict:
        """Generate minimal but valid Power BI template structure"""
        
        # Get table and column info from Tableau
        table_name = "SampleData"
        columns = []
        
        if tableau_data.get('datasources'):
            ds = tableau_data['datasources'][0]
            connection = ds.get('connection', {})
            # Use the datasource name or schema as table name
            table_name = ds.get('name', connection.get('schema', 'SampleData'))
            if table_name.startswith('federated.'):
                table_name = "SampleData"  # Clean up federated names
            
            # Deduplicate columns by name
            seen_columns = set()
            for col in ds.get('columns', []):
                col_name = col.get('name', '').replace('[', '').replace(']', '')
                if (col_name and not col_name.startswith('Measure') and 
                    col_name.strip() and col_name not in seen_columns):
                    columns.append({
                        'name': col_name,
                        'dataType': self._map_powerbi_datatype(col.get('datatype', 'string'))
                    })
                    seen_columns.add(col_name)
                    if len(columns) >= 10:  # Limit to 10 columns
                        break
        
        # If no valid columns found, create sample ones
        if not columns:
            columns = [
                {'name': 'Category', 'dataType': 'string'},
                {'name': 'Value', 'dataType': 'double'}
            ]
        
        # Get enhanced connection information from Tableau
        connection_info = {}
        if tableau_data.get('datasources'):
            ds = tableau_data['datasources'][0]
            connection_info = ds.get('connection', {})
            
        # Generate enhanced M query based on connection type
        m_query = self._generate_enhanced_m_query(table_name, connection_info)
        
        print(f"📋 Using table name: {table_name}")
        print(f"📋 Generated {len(columns)} columns: {[col['name'] for col in columns]}")
        print(f"🔗 Connection type: {connection_info.get('class', 'unknown')}")
        
        # Data Model Schema - Fixed structure for Power BI compatibility
        data_model_schema = {
            "version": "1.0",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True
            },
            "name": "SemanticModel",
            "compatibilityLevel": 1567,
            "defaultLocale": "en-US",
            "dataSources": [
                {
                    "type": "structured",
                    "name": "DataSource1", 
                    "connectionDetails": {
                        "protocol": "tds",
                        "address": {
                            "server": "localhost",
                            "database": "SampleDB"
                        },
                        "authentication": None,
                        "query": None
                    },
                    "options": {
                        "includeRelationshipColumns": False,
                        "privacy": "Public"
                    },
                    "credential": {
                        "AuthenticationKind": "UsernamePassword",
                        "kind": "SQL",
                        "path": "localhost;SampleDB",
                        "Username": "TableauUser"
                    }
                }
            ],
            "model": {
                "name": "SemanticModel",
                "description": "Converted from Tableau workbook",
                "culture": "en-US",
                "defaultLocale": "en-US",
                "collation": "Latin1_General_CI_AS",
                "dataAccessOptions": {
                    "legacyRedirects": True,
                    "returnErrorValuesAsNull": True
                },
                "tables": [
                    {
                        "name": table_name,
                        "lineageTag": str(uuid.uuid4()),
                        "columns": [
                            {
                                "name": col['name'],
                                "lineageTag": str(uuid.uuid4()),
                                "dataType": col['dataType'],
                                "sourceColumn": col['name'],
                                "summarizeBy": "none" if col['dataType'] == "string" else "sum",
                                "displayOrdinal": idx
                            }
                            for idx, col in enumerate(columns)
                        ],
                        "partitions": [
                            {
                                "name": f"{table_name}-Partition",
                                "mode": "import",
                                "dataView": "full",
                                "source": {
                                    "type": "m",
                                    "expression": m_query
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        # Report Layout - Fixed structure for Power BI compatibility  
        report_id = str(uuid.uuid4())
        section_id = str(uuid.uuid4())
        
        report_layout = {
            "id": report_id,
            "displayName": "Converted Tableau Report",
            "description": "Report converted from Tableau workbook",
            "pages": [
                {
                    "id": section_id,
                    "displayName": "Page 1",
                    "width": 1280,
                    "height": 720,
                    "displayOption": 1,
                    "visualContainers": [],
                    "filters": [],
                    "config": {
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
                    }
                }
            ],
            "config": {
                "theme": {
                    "name": "CityPark"
                },
                "layoutType": 0,
                "objects": {
                    "section": [
                        {
                            "properties": {
                                "page": {
                                    "background": [
                                        {
                                            "color": {
                                                "solid": {
                                                    "color": "#FFFFFF"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            },
            "resourcePackages": [
                {
                    "resourcePackage": {
                        "type": "ResourcePackage",
                        "items": [
                            {
                                "type": "Report",
                                "displayName": "Report",
                                "id": report_id
                            }
                        ]
                    }
                }
            ]
        }
        
        # Add a simple visualization if we have worksheet data
        if tableau_data.get('worksheets') and columns:
            visual_id = str(uuid.uuid4())
            
            # Get the first worksheet for analysis
            worksheet = tableau_data['worksheets'][0]
            visual_type = self._get_tableau_visual_type(worksheet)
            
            # Try to find category and value fields
            category_field = columns[0]['name']
            value_field = columns[1]['name'] if len(columns) > 1 else columns[0]['name']
            
            # Check Tableau worksheet for better field mapping
            encodings = worksheet.get('encodings', {})
            for attr, encoding in encodings.items():
                field = encoding.get('field', '').replace('[', '').replace(']', '')
                if field and any(col['name'] == field for col in columns):
                    if attr in ['x', 'columns']:
                        category_field = field
                    elif attr in ['y', 'rows']:
                        value_field = field
            
            print(f"📊 Creating {visual_type} visual: {category_field} vs {value_field}")
            
            # Create a proper visual container for Power BI
            visual_container = {
                "id": visual_id,
                "x": 50,
                "y": 50,
                "z": 1000,
                "width": 600,
                "height": 400,
                "config": {
                    "name": visual_id,
                    "layouts": [
                        {
                            "id": 0,
                            "position": {
                                "x": 50,
                                "y": 50,
                                "z": 1000,
                                "width": 600,
                                "height": 400
                            }
                        }
                    ],
                    "singleVisual": {
                        "visualType": visual_type,
                        "projections": {
                            "Category": [
                                {
                                    "queryRef": f"{table_name}.{category_field}",
                                    "active": True
                                }
                            ],
                            "Y": [
                                {
                                    "queryRef": f"{table_name}.{value_field}",
                                    "active": True
                                }
                            ]
                        },
                        "prototypeQuery": {
                            "Version": 2,
                            "From": [
                                {
                                    "Name": "t", 
                                    "Entity": table_name,
                                    "Type": 0
                                }
                            ],
                            "Select": [
                                {
                                    "Column": {
                                        "Expression": {
                                            "SourceRef": {
                                                "Source": "t"
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
                                                        "Source": "t" 
                                                    }
                                                },
                                                "Property": value_field
                                            }
                                        },
                                        "Function": 1
                                    },
                                    "Name": f"Sum({table_name}.{value_field})"
                                }
                            ]
                        }
                    }
                }
            }
            
            # Add the visual to the page
            report_layout['pages'][0]['visualContainers'].append(visual_container)
        
        # Create metadata structure
        metadata = {
            "version": "4.0",
            "culture": "en-US",
            "modifiedTime": "2024-01-01T00:00:00.000Z"
        }
        
        return {
            'DataModelSchema': data_model_schema,
            'Layout': report_layout,
            'Version': '4.0',
            'Settings': {
                "useStylableVisualContainerHeader": True,
                "exportDataMode": 1,
                "useNewFilterPaneExperience": True
            },
            'Metadata': metadata
        }
    
    
    def _validate_pbit_structure(self, temp_dir: str):
        """Validate the generated Power BI template structure"""
        required_files = ['DataModelSchema', 'Version', 'Settings', 'Metadata']
        required_dirs = ['Report']
        
        print("🔍 Validating file structure...")
        
        # Check required files
        for file_name in required_files:
            file_path = os.path.join(temp_dir, file_name)
            if not os.path.exists(file_path):
                raise ValueError(f"Missing required file: {file_name}")
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise ValueError(f"Empty required file: {file_name}")
            print(f"  ✅ {file_name} ({file_size} bytes)")
        
        # Check required directories and their contents
        for dir_name in required_dirs:
            dir_path = os.path.join(temp_dir, dir_name)
            if not os.path.exists(dir_path):
                raise ValueError(f"Missing required directory: {dir_name}")
            
            # Check Layout file in Report directory
            layout_path = os.path.join(dir_path, 'Layout')
            if not os.path.exists(layout_path):
                raise ValueError("Missing Layout file in Report directory")
            
            layout_size = os.path.getsize(layout_path)
            print(f"  ✅ {dir_name}/Layout ({layout_size} bytes)")
        
        # Validate JSON structure by attempting to parse key files
        print("🔍 Validating JSON structures...")
        
        # Validate DataModelSchema
        try:
            with open(os.path.join(temp_dir, 'DataModelSchema'), 'rb') as f:
                content = f.read()[2:]  # Skip BOM
                json_content = json.loads(content.decode('utf-16le'))
                if 'model' not in json_content:
                    raise ValueError("DataModelSchema missing 'model' section")
                print("  ✅ DataModelSchema JSON is valid")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in DataModelSchema: {e}")
        
        # Validate Layout
        try:
            with open(os.path.join(temp_dir, 'Report', 'Layout'), 'rb') as f:
                content = f.read()[2:]  # Skip BOM
                json_content = json.loads(content.decode('utf-16le'))
                if 'pages' not in json_content:
                    raise ValueError("Layout missing 'pages' section")
                print("  ✅ Layout JSON is valid")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Layout: {e}")
        
        print("✅ All validations passed!")
    
    def _get_tableau_visual_type(self, worksheet_data: Dict) -> str:
        """Determine the best Power BI visual type based on Tableau worksheet data"""
        # Check Tableau marks for visual type hints
        marks = worksheet_data.get('marks', [])
        encodings = worksheet_data.get('encodings', {})
        
        # Default to column chart
        visual_type = "columnChart"
        
        for mark in marks:
            mark_class = mark.get('class', '').lower()
            if mark_class in ['bar', 'automatic']:
                visual_type = "columnChart"
            elif mark_class in ['line']:
                visual_type = "lineChart"
            elif mark_class in ['circle', 'shape']:
                visual_type = "scatterChart"
            elif mark_class in ['square', 'ganttbar']:
                visual_type = "barChart"
            elif mark_class in ['text']:
                visual_type = "table"
            elif mark_class in ['map']:
                visual_type = "map"
            break
        
        # Override based on encodings if more specific info available
        if 'color' in encodings and 'size' in encodings:
            visual_type = "scatterChart"
        elif len(encodings) >= 3:
            visual_type = "table"  # Multiple encodings suggest tabular data
        
        return visual_type
    
    def _generate_enhanced_m_query(self, table_name: str, connection_info: Dict) -> str:
        """Generate more sophisticated M query based on connection information"""
        
        # Extract connection details
        conn_class = connection_info.get('class', '').lower()
        server = connection_info.get('server', 'localhost')
        database = connection_info.get('dbname', 'SampleDB')
        port = connection_info.get('port', '')
        schema = connection_info.get('schema', 'dbo')
        
        if conn_class == 'oracle':
            # Oracle-specific M query
            if port:
                server_with_port = f"{server}:{port}"
            else:
                server_with_port = server
                
            m_query = f'''let
    Source = Oracle.Database("{server_with_port}", "{database}"),
    {schema}_{table_name} = Source{{[Schema="{schema}",Item="{table_name}"]}}[Data]
in
    {schema}_{table_name}'''
        
        elif conn_class == 'mysql':
            # MySQL-specific M query  
            m_query = f'''let
    Source = MySQL.Database("{server}", "{database}"),
    {table_name}_Table = Source{{[Name="{table_name}"]}}[Data]
in
    {table_name}_Table'''
        
        elif conn_class == 'postgresql':
            # PostgreSQL-specific M query
            m_query = f'''let
    Source = PostgreSQL.Database("{server}", "{database}"),
    {schema}_{table_name} = Source{{[Schema="{schema}",Item="{table_name}"]}}[Data]
in
    {schema}_{table_name}'''
        
        else:
            # Default SQL Server M query
            m_query = f'''let
    Source = Sql.Database("{server}", "{database}"),
    {schema}_{table_name} = Source{{[Schema="{schema}",Item="{table_name}"]}}[Data]
in
    {schema}_{table_name}'''
        
        return m_query
    
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
            
            print(f"🔧 Creating Power BI template structure in {temp_dir}")
            
            # Write DataModelSchema (UTF-16 LE with BOM, no line breaks)
            print("📝 Writing DataModelSchema...")
            with open(os.path.join(temp_dir, 'DataModelSchema'), 'wb') as f:
                # Write BOM for UTF-16 LE
                f.write(b'\xff\xfe')
                # Write JSON without formatting
                json_str = json.dumps(template_structure['DataModelSchema'], ensure_ascii=False, separators=(',', ':'))
                f.write(json_str.encode('utf-16le'))
            
            # Create Report directory and write Layout
            report_dir = os.path.join(temp_dir, 'Report')
            os.makedirs(report_dir, exist_ok=True)
            
            print("📝 Writing Layout...")
            with open(os.path.join(report_dir, 'Layout'), 'wb') as f:
                # Write BOM for UTF-16 LE
                f.write(b'\xff\xfe')
                # Write JSON without formatting
                json_str = json.dumps(template_structure['Layout'], ensure_ascii=False, separators=(',', ':'))
                f.write(json_str.encode('utf-16le'))
            
            # Write Version (UTF-8, no BOM)
            print("📝 Writing Version...")
            with open(os.path.join(temp_dir, 'Version'), 'w', encoding='utf-8') as f:
                f.write(template_structure['Version'])
            
            # Write Settings (UTF-16 LE with BOM)
            print("📝 Writing Settings...")
            with open(os.path.join(temp_dir, 'Settings'), 'wb') as f:
                # Write BOM for UTF-16 LE
                f.write(b'\xff\xfe')
                # Write JSON without formatting
                json_str = json.dumps(template_structure['Settings'], ensure_ascii=False, separators=(',', ':'))
                f.write(json_str.encode('utf-16le'))
            
            # Write Metadata (UTF-16 LE with BOM) - This is required for proper .pbit files
            print("📝 Writing Metadata...")
            with open(os.path.join(temp_dir, 'Metadata'), 'wb') as f:
                # Write BOM for UTF-16 LE  
                f.write(b'\xff\xfe')
                # Write JSON without formatting
                json_str = json.dumps(template_structure['Metadata'], ensure_ascii=False, separators=(',', ':'))
                f.write(json_str.encode('utf-16le'))
            
            # Validate generated files
            print("🔍 Validating generated files...")
            self._validate_pbit_structure(temp_dir)
            
            # Create the .pbit file (ZIP archive with standard compression)
            print("📦 Creating .pbit ZIP archive...")
            with zipfile.ZipFile(pbit_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, arc_name)
                        print(f"  ➕ Added {arc_name}")
            
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir)
            
            # Final validation
            file_size = os.path.getsize(pbit_path)
            print(f"\n✅ Power BI template created successfully!")
            print(f"📁 File: {pbit_path}")
            print(f"📊 Size: {file_size} bytes")
            print(f"🎯 Ready to open in Power BI Desktop!")
            print(f"💡 The template will prompt you to connect to your data source.")
            
            return pbit_path
            
        except Exception as e:
            print(f"❌ Error creating .pbit file: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_pbit_compatibility(self, pbit_path: str) -> bool:
        """Test the generated .pbit file for Power BI compatibility"""
        try:
            print(f"\n🧪 Testing Power BI compatibility: {pbit_path}")
            
            # Test 1: Check if ZIP file is valid
            with zipfile.ZipFile(pbit_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                print(f"  ✅ ZIP file is valid ({len(file_list)} files)")
                
                # Test 2: Check required files are present
                required_files = ['DataModelSchema', 'Version', 'Settings', 'Metadata', 'Report/Layout']
                for req_file in required_files:
                    if req_file not in file_list:
                        print(f"  ❌ Missing required file: {req_file}")
                        return False
                print("  ✅ All required files present")
                
                # Test 3: Check file encodings and JSON validity
                for file_name in file_list:
                    if file_name == 'Version':
                        # Version should be UTF-8
                        content = zip_file.read(file_name)
                        version = content.decode('utf-8')
                        if not version.strip():
                            print(f"  ❌ Version file is empty")
                            return False
                        print(f"  ✅ Version: {version.strip()}")
                    else:
                        # Other files should be UTF-16 LE with BOM and valid JSON
                        content = zip_file.read(file_name)
                        if len(content) < 3 or content[:2] != b'\xff\xfe':
                            print(f"  ❌ {file_name} missing UTF-16 LE BOM")
                            return False
                        
                        try:
                            json_content = json.loads(content[2:].decode('utf-16le'))
                            print(f"  ✅ {file_name} is valid JSON ({len(content)} bytes)")
                        except (json.JSONDecodeError, UnicodeDecodeError) as e:
                            print(f"  ❌ {file_name} JSON parse error: {e}")
                            return False
                
                # Test 4: Check DataModelSchema structure
                content = zip_file.read('DataModelSchema')
                schema = json.loads(content[2:].decode('utf-16le'))
                
                required_schema_fields = ['version', 'name', 'model']
                for field in required_schema_fields:
                    if field not in schema:
                        print(f"  ❌ DataModelSchema missing field: {field}")
                        return False
                
                if 'tables' not in schema['model']:
                    print(f"  ❌ DataModelSchema.model missing 'tables'")
                    return False
                
                tables = schema['model']['tables']
                if not tables:
                    print(f"  ❌ No tables in DataModelSchema")
                    return False
                
                table = tables[0]
                if 'columns' not in table or not table['columns']:
                    print(f"  ❌ Table has no columns")
                    return False
                
                print(f"  ✅ DataModelSchema structure valid ({len(table['columns'])} columns)")
                
                # Test 5: Check Layout structure
                content = zip_file.read('Report/Layout')
                layout = json.loads(content[2:].decode('utf-16le'))
                
                if 'pages' not in layout:
                    print(f"  ❌ Layout missing 'pages'")
                    return False
                
                if not layout['pages']:
                    print(f"  ❌ Layout has no pages")
                    return False
                
                page = layout['pages'][0]
                required_page_fields = ['id', 'width', 'height']
                for field in required_page_fields:
                    if field not in page:
                        print(f"  ❌ Page missing field: {field}")
                        return False
                
                print(f"  ✅ Layout structure valid ({len(layout['pages'])} pages)")
                
            print("  🎉 All compatibility tests passed!")
            return True
            
        except Exception as e:
            print(f"  ❌ Compatibility test failed: {e}")
            return False
    
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
            template_structure = self.generate_minimal_pbit_structure(self.tableau_data)
            
            # Create .pbit file
            print("Creating Power BI template file...")
            pbit_path = self.create_pbit_file(template_structure, output_dir, base_name)
            
            if pbit_path:
                # Run compatibility test
                if self.test_pbit_compatibility(pbit_path):
                    print("\n🎉 Conversion completed successfully!")
                    print("✅ Generated .pbit file passed all compatibility tests!")
                else:
                    print("\n⚠️  Conversion completed with warnings!")
                    print("🔍 Generated .pbit file may have compatibility issues!")
                return True
            else:
                print("Error: Failed to create .pbit file")
                return False
            
        except Exception as e:
            print(f"Error during conversion: {e}")
            import traceback
            traceback.print_exc()
            return False

def create_test_tableau_files():
    """Create test Tableau files for testing different scenarios"""
    
    # Test file 1: Oracle connection with bar chart
    oracle_twb = '''<?xml version='1.0' encoding='utf-8' ?>
<workbook version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <datasources>
    <datasource caption='Sales Data' inline='true' name='oracle.salesdb' version='18.1'>
      <connection class='oracle' dbname='SALESDB' port='1521' server='oracle-server' username='sales_user' schema='SALES' />
      <column datatype='string' name='[Product_Category]' role='dimension' type='nominal' />
      <column datatype='real' name='[Sales_Amount]' role='measure' type='quantitative' />
      <column datatype='date' name='[Order_Date]' role='dimension' type='ordinal' />
      <column datatype='string' name='[Region]' role='dimension' type='nominal' />
    </datasource>
  </datasources>
  <worksheets>
    <worksheet name='Sales by Category'>
      <table>
        <panes>
          <pane>
            <mark class='Bar' />
            <encodings>
              <color column='[oracle.salesdb].[Product_Category]' />
              <size column='[oracle.salesdb].[Sales_Amount]' />
            </encodings>
          </pane>
        </panes>
      </table>
    </worksheet>
  </worksheets>
</workbook>'''
    
    # Test file 2: MySQL connection with line chart  
    mysql_twb = '''<?xml version='1.0' encoding='utf-8' ?>
<workbook version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <datasources>
    <datasource caption='Time Series' inline='true' name='mysql.analytics' version='18.1'>
      <connection class='mysql' dbname='analytics' port='3306' server='mysql-server' username='analyst' />
      <column datatype='date' name='[Date]' role='dimension' type='ordinal' />
      <column datatype='real' name='[Revenue]' role='measure' type='quantitative' />
      <column datatype='integer' name='[Orders]' role='measure' type='quantitative' />
    </datasource>
  </datasources>
  <worksheets>
    <worksheet name='Revenue Trend'>
      <table>
        <panes>
          <pane>
            <mark class='Line' />
            <encodings>
              <columns column='[mysql.analytics].[Date]' />
              <rows column='[mysql.analytics].[Revenue]' />
            </encodings>
          </pane>
        </panes>
      </table>
    </worksheet>
  </worksheets>
</workbook>'''
    
    # Write test files
    with open('/tmp/test_oracle.twb', 'w') as f:
        f.write(oracle_twb)
    
    with open('/tmp/test_mysql.twb', 'w') as f:
        f.write(mysql_twb)
    
    print("📝 Created test Tableau files:")
    print("  - /tmp/test_oracle.twb (Oracle + Bar chart)")
    print("  - /tmp/test_mysql.twb (MySQL + Line chart)")

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
