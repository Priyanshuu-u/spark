# Tableau to Power BI Converter

Converts Tableau .twbx files to actual Power BI template (.pbit) files that can be opened directly in Power BI Desktop.

## Features

- **Direct Conversion**: Generates actual Power BI template (.pbit) files instead of instruction files
- **Data Source Support**: Handles Oracle, SQL Server, MySQL, and PostgreSQL connections
- **Visualization Conversion**: Converts Tableau visualizations to Power BI visuals
- **Dashboard Layout**: Preserves dashboard structure and layout information
- **Ready to Use**: Generated .pbit files can be opened directly in Power BI Desktop

## Requirements

- Python 3.6+
- No additional dependencies required (uses only standard library)

## Usage

```bash
# Convert a Tableau workbook file
python App.py input.twbx

# Convert with custom output directory
python App.py input.twbx -o /path/to/output

# Convert .twb file directly
python App.py input.twb
```

## Output

The converter generates a `.pbit` (Power BI Template) file that contains:

- **DataModelSchema**: JSON describing the data model and connections
- **DiagramLayout**: JSON describing the report layout structure
- **Report/Layout**: JSON describing visualizations and their configurations
- **Settings**: JSON with report settings and preferences
- **Version**: Power BI version information

## Power BI Template Structure

Power BI templates (.pbit) are ZIP files containing structured JSON files that define:

1. **Data Sources**: Connection strings and authentication details
2. **Data Model**: Tables, columns, relationships, and measures
3. **Visualizations**: Charts, graphs, and their field mappings
4. **Layout**: Page layout, visual positioning, and formatting
5. **Settings**: Report-level configurations and preferences

## Supported Tableau Features

- **Data Sources**: Oracle, SQL Server, MySQL, PostgreSQL
- **Visualizations**: Bar charts, line charts, area charts, pie charts
- **Dashboards**: Layout preservation and zone mapping
- **Fields**: Dimensions, measures, and calculated fields
- **Connections**: Database connections and authentication

## Examples

### Basic Conversion
```bash
python App.py sales_dashboard.twbx
# Output: sales_dashboard.pbit
```

### With Custom Output Directory
```bash
python App.py reports/quarterly.twbx -o converted/
# Output: converted/quarterly.pbit
```

## Opening in Power BI Desktop

1. Double-click the generated `.pbit` file
2. Power BI Desktop will open with the converted dashboard
3. Configure data source credentials if needed
4. Refresh data to load your actual data
5. Customize and enhance as needed

## Notes

- The converter focuses on structural conversion rather than pixel-perfect replication
- Data source credentials will need to be reconfigured in Power BI Desktop
- Complex calculated fields may require manual adjustment
- Custom visualizations may be converted to standard Power BI chart types