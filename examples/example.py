from planpro_importer import reader
from sumoexporter import SUMOExporter
from railwayroutegenerator.routegenerator import RouteGenerator

reader = reader.PlanProReader("MVP")
topology = reader.read_topology_from_plan_pro_file()

generator = RouteGenerator(topology)
topology.routes = generator.generate_routes()

sumo_exporter = SUMOExporter(topology)
sumo_exporter.convert()
sumo_exporter.write_output()
