
patch_dict ={
				'saiw':
					{'type': 'patch',
					 'label': 'SAIW',
					 'label_coords': (34.8, 5.3),
					 'patch_coords': ([34.78,34.99,34.8,34.6,34.78], [6.6,5,4,5.5,6.6])
					},
				'lsw':
					{'type': 'patch',
					 'label': 'LSW',
					 'label_coords': (34.85, 3.3),
					 'patch_coords': ([34.8,34.89,34.89,34.8,34.8], [3.0,3.0,3.6,3.6,3.0])
					},
				'neadw':
					{'type': 'patch',
					 'label': 'NEADW',
					 'label_coords': (34.925, 2.5),
					 'patch_coords': ([34.89,34.89,34.89,34.94,34.94], [2.03,2.03,2.5,2.5,2.03])
					},
			}
box_dict = {
				'aabw':
					{'type': 'BoxAnnotation',
					 'label': 'AABW/LDW',
					 'label_coords': (34.8, 2.0),
					 'box_coords': {'top': 2.5, 
                                    'right': 34.9,
                                    'bottom': None,
                                    'left': None,
                                    }
					},
				'isow':
					{'type': 'BoxAnnotation',
					 'label': 'ISOW',
					 'label_coords': (35.3, 2.0),
					 'box_coords': {'top': 2.5,
                                    'right': None,
                                    'bottom': None,
                                    'left': 34.98,
                                   }
					},
			}