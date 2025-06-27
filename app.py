from flask import Flask, request, Response
import os
from collections import defaultdict

app = Flask(__name__)

def load_areas_grouped(file_path):
    departments = defaultdict(list)
    current_dept = None
    city = None
    code = None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith('DepartementName:'):
                    current_dept = stripped.split(':', 1)[1].strip()
                elif stripped.startswith('CityName:'):
                    city = stripped.split(':', 1)[1].strip()
                elif stripped.startswith('Code:'):
                    code = stripped.split(':', 1)[1].strip()
                    if current_dept and city and code:
                        departments[current_dept].append({
                            'areaName': city,
                            'areaCode': code
                        })
                        city = code = None
    except FileNotFoundError:
        print("Areas.txt file not found.")
    return departments

def load_area_places(file_path):
    areas = defaultdict(list)
    area_names = {}
    current_area = None
    current_block = {}

    def flush_block():
        if current_area:
            name = current_block.get('AreaName', '').strip()
            code = current_block.get('AreaCode', '').strip()
            if name and code:
                areas[current_area].append({
                    'areaName': name,
                    'areaCode': code,
                    'kanji1': current_block.get('kanji1', ''),
                    'kanji2': current_block.get('Kanji2', ''),
                    'kanji3': current_block.get('Kanji3', ''),
                    'kanji4': current_block.get('Kanji4', ''),
                    'display': current_block.get('display', '1'),
                    'isNextArea': current_block.get('isNextArea', '0')
                })

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("Area:"):
                    flush_block()
                    current_area = stripped.split(':', 1)[1].strip()
                    current_block = {}
                elif stripped.startswith("Name of Area:") and current_area:
                    name_value = stripped.split(':', 1)[1].strip()
                    if name_value:
                        area_names[current_area] = name_value
                elif ':' in stripped:
                    key, value = stripped.split(':', 1)
                    current_block[key.strip()] = value.strip()
                elif not stripped:
                    flush_block()
                    current_block = {}
        flush_block()
    except FileNotFoundError:
        print("Adress.txt file not found.")
    return areas, area_names

@app.route('/nwapi.php')
def nwapi():
    action = request.args.get('action')
    platform = request.args.get('platform')
    area_code = request.args.get('areaCode')
    reservation_type = request.args.get('reservationType')
    
    if action == 'webApi_document_template':
        eula_path = os.path.join(app.root_path, 'assets', 'eula.txt')
        try:
            with open(eula_path, 'r', encoding='utf-8') as f:
                eula_content = f.read()
        except FileNotFoundError:
            eula_content = 'EULA not found.'

        response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
  <container0>
    <contents><![CDATA[{eula_content}]]></contents>
  </container0>
  <container1>
    <contents><![CDATA[no seriously, stop trying]]></contents>
  </container1>
  <container2>
    <contents><![CDATA[the heck are you doing]]></contents>
  </container2>
  <apiStatus>
    <code><![CDATA[0]]></code>
  </apiStatus>
  <version><![CDATA[1]]></version>
</response>"""
        return Response(response_xml, mimetype='application/xml')

    elif action == 'webApi_area_list':
        if platform == 'wii' and area_code and area_code != '0':
            address_path = os.path.join(app.root_path, 'assets', 'Adress.txt')
            areas_by_code, area_name_map = load_area_places(address_path)
            selected_areas = areas_by_code.get(area_code, [])
            segment_name = area_name_map.get(area_code, f"Area {area_code}")

            list_items = "".join(f"""
        <areaPlace>
          <areaName><![CDATA[{place['areaName']}]]></areaName>
          <areaCode><![CDATA[{place['areaCode']}]]></areaCode>
          <isNextArea><![CDATA[{place['isNextArea']}]]></isNextArea>
          <display><![CDATA[{place['display']}]]></display>
          <kanji1><![CDATA[{place['kanji1']}]]></kanji1>
          <kanji2><![CDATA[{place['kanji2']}]]></kanji2>
          <kanji3><![CDATA[{place['kanji3']}]]></kanji3>
          <kanji4><![CDATA[{place['kanji4']}]]></kanji4>
        </areaPlace>""" for place in selected_areas)

            response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
  <areaList>
    <place>
      <segment><![CDATA[{segment_name}]]></segment>
      <list>{list_items}
      </list>
    </place>
  </areaList>
  <areaCount><![CDATA[{len(selected_areas)}]]></areaCount>
  <apiStatus>
    <code><![CDATA[0]]></code>
  </apiStatus>
  <version><![CDATA[1]]></version>
</response>"""
            return Response(response_xml, mimetype='application/xml')

        else:
            areas_by_dept = load_areas_grouped(os.path.join(app.root_path, 'assets', 'Areas.txt'))
            area_list_xml = ""
            for dept, places in areas_by_dept.items():
                list_items = "".join(f"""
        <areaPlace>
          <areaName><![CDATA[{p['areaName']}]]></areaName>
          <areaCode><![CDATA[{p['areaCode']}]]></areaCode>
        </areaPlace>""" for p in places)
                area_list_xml += f"""
    <place>
      <segment><![CDATA[{dept}]]></segment>
      <list>{list_items}
      </list>
    </place>"""

            total_places = sum(len(v) for v in areas_by_dept.values())
            response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
  <areaList>{area_list_xml}
  </areaList>
  <areaCount><![CDATA[{total_places}]]></areaCount>
  <apiStatus>
    <code><![CDATA[0]]></code>
  </apiStatus>
  <version><![CDATA[1]]></version>
  <selectedArea>
  <areaCode><![CDATA[1]]></areaCode>
</selectedArea>
</response>"""
            return Response(response_xml, mimetype='application/xml')
    
    elif action == 'webApi_category_list' and platform == 'wii' and area_code and reservation_type:
        response_xml = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <Pizza>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[01]]></CategoryCode></TestingCategory>
    </CategoryList>
  </Pizza>
  <Bento>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[02]]></CategoryCode></TestingCategory>
    </CategoryList>
  </Bento>
  <Sushi>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[03]]></CategoryCode></TestingCategory>
    </CategoryList>
  </Sushi>
  <Fish>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[04]]></CategoryCode></TestingCategory>
    </CategoryList>
  </Fish>
  <Seafood>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[05]]></CategoryCode></TestingCategory>
    </CategoryList>
  </Seafood>
  <American>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[06]]></CategoryCode></TestingCategory>
    </CategoryList>
  </American>
  <Fast>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[07]]></CategoryCode></TestingCategory>
    </CategoryList>
  </Fast>
  <Indian>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[08]]></CategoryCode></TestingCategory>
    </CategoryList>
  </Indian>
  <Party>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[09]]></CategoryCode></TestingCategory>
    </CategoryList>
  </Party>
  <Drinks>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[10]]></CategoryCode></TestingCategory>
    </CategoryList>
  </Drinks>
  <Placeholder>
    <LargeCategoryName><![CDATA[Meal]]></LargeCategoryName>
    <CategoryList>
      <TestingCategory><CategoryCode><![CDATA[11]]></CategoryCode></TestingCategory>
    </CategoryList>
  </Placeholder>
</response>
<apiStatus>
  <code><![CDATA[0]]></code>
</apiStatus>
<version><![CDATA[1]]></version>"""
    return Response(response_xml, mimetype='application/xml')
    
    return 'Invalid action or parameters', 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
