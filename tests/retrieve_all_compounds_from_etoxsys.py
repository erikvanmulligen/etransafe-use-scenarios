from kh.api import KnowledgeHubAPI

def main():
	api = KnowledgeHubAPI()
	api.login('erik.mulligen', 'Crosby99!')
	print('compoundIdentifier\torganisation\tinchi\tsmiles')
	for compound in api.eToxSys().getAllCompounds():
		id = compound['compoundIdentifier'].strip()
		organisation = compound['organisation'].strip()
		inchi = (compound['inchi'] if compound['inchi'] is not None else '').replace('\n', '').strip()
		smiles = (compound['smiles'] if compound['smiles'] is not None else '').replace('\n', '').strip()
		print(f'{id} \t{organisation} \t{inchi} \t{smiles} ')


if __name__ == "__main__":
	main()