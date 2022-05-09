import sys
from converter import Converter

if __name__ == "__main__":
    plan_pro_file_name = sys.argv[1]
    generate_routes = "--generate-routes" in sys.argv

    output_format = "sumo-plain-xml"
    if "--output-format" in sys.argv:
        index_output_format = sys.argv.index("--output-format")
        output_format = sys.argv[index_output_format + 1]

    converter = Converter(plan_pro_file_name)
    converter.convert()
    converter.write_output(output_format)

