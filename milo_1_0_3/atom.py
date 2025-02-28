#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Module for representing and manipulating atomic data."""

from typing import ClassVar, Dict, Tuple, Union

# Default data for isotope with largest isotopic composition.
# If all isotopes are radioactive, the listed isotope with the smallest mass
# was chosen. (For these atoms, users should not rely on these dafaults.)
# Reference:
#   Coursey, J.S., Schwab, D.J., Tsai, J.J., and Dragoset, R.A. (2015), Atomic
#   Weights and Isotopic Compositions (version 4.1). [Online] Available:
#   http://physics.nist.gov/Comp [2020 Aug. 06]. National Institute of
#   Standards and Technology, Gaithersburg, MD.
default_from_symbol = {
	# 'Symbol': (atomic_number, mass_number, mass),
	"H": (1, 1, 1.00782503223),
	"He": (2, 4, 4.00260325413),
	"Li": (3, 7, 7.0160034366),
	"Be": (4, 9, 9.012183065),
	"B": (5, 11, 11.00930536),
	"C": (6, 12, 12.0000000),
	"N": (7, 14, 14.00307400443),
	"O": (8, 16, 15.99491461957),
	"F": (9, 19, 18.99840316273),
	"Ne": (10, 20, 19.9924401762),
	"Na": (11, 23, 22.9897692820),
	"Mg": (12, 24, 23.985041697),
	"Al": (13, 27, 26.98153853),
	"Si": (14, 28, 27.97692653465),
	"P": (15, 31, 30.97376199842),
	"S": (16, 32, 31.9720711744),
	"Cl": (17, 35, 34.968852682),
	"Ar": (18, 40, 39.9623831237),
	"K": (19, 39, 38.9637064864),
	"Ca": (20, 40, 39.9625906),
	"Sc": (21, 45, 44.9559083),
	"Ti": (22, 48, 47.9479409),
	"V": (23, 51, 50.9439570),
	"Cr": (24, 52, 51.9405062),
	"Mn": (25, 55, 54.9380439),
	"Fe": (26, 56, 55.9349363),
	"Co": (27, 59, 58.9331943),
	"Ni": (28, 58, 57.9353424),
	"Cu": (29, 63, 62.9295977),
	"Zn": (30, 64, 63.9291420),
	"Ga": (31, 69, 68.9255735),
	"Ge": (32, 74, 73.9211774),
	"As": (33, 75, 74.9215945),
	"Se": (34, 80, 79.9165196),
	"Br": (35, 79, 78.9183361),
	"Kr": (36, 84, 83.911507),
	"Rb": (37, 85, 84.911789),
	"Sr": (38, 88, 87.905612),
	"Y": (39, 89, 88.905848),
	"Zr": (40, 90, 89.904704),
	"Nb": (41, 93, 92.906378),
	"Mo": (42, 98, 97.905408),
	"Tc": (43, 98, 97.907216),
	"Ru": (44, 101, 100.905582),
	"Rh": (45, 103, 102.905504),
	"Pd": (46, 106, 105.903486),
	"Ag": (47, 107, 106.905097),
	"Cd": (48, 114, 113.903358),
	"In": (49, 115, 114.903879),
	"Sn": (50, 120, 119.902202),
	"Sb": (51, 121, 120.903816),
	"Te": (52, 130, 129.906224),
	"I": (53, 127, 126.904473),
	"Xe": (54, 132, 131.904155),
	"Cs": (55, 133, 132.905452),
	"Ba": (56, 138, 137.905247),
	"La": (57, 139, 138.906353),
	"Ce": (58, 140, 139.905439),
	"Pr": (59, 141, 140.907653),
	"Nd": (60, 142, 141.907723),
	"Pm": (61, 145, 144.912749),
	"Sm": (62, 152, 151.919732),
	"Eu": (63, 153, 152.921230),
	"Gd": (64, 158, 157.924104),
	"Tb": (65, 159, 158.925347),
	"Dy": (66, 164, 163.929175),
	"Ho": (67, 165, 164.930322),
	"Er": (68, 166, 165.930293),
	"Tm": (69, 169, 168.934213),
	"Yb": (70, 174, 173.938862),
	"Lu": (71, 175, 174.940771),
	"Hf": (72, 180, 179.946550),
	"Ta": (73, 181, 180.947996),
	"W": (74, 184, 183.950933),
	"Re": (75, 187, 186.955751),
	"Os": (76, 192, 191.961479),
	"Ir": (77, 193, 192.962924),
	"Pt": (78, 195, 194.964774),
	"Au": (79, 197, 196.966569),
	"Hg": (80, 202, 201.970643),
	"Tl": (81, 205, 204.974428),
	"Pb": (82, 208, 207.976652),
	"Bi": (83, 209, 208.980399),
	"Po": (84, 209, 208.982430),
	"At": (85, 210, 209.987148),
	"Rn": (86, 222, 222.017578),
	"Fr": (87, 223, 223.019736),
	"Ra": (88, 226, 226.025410),
	"Ac": (89, 227, 227.027747),
	"Th": (90, 232, 232.038055),
	"Pa": (91, 231, 231.035882),
	"U": (92, 238, 238.050786),
	"Np": (93, 237, 237.048173),
	"Pu": (94, 244, 244.064204),
	"Am": (95, 243, 243.061381),
	"Cm": (96, 247, 247.070353),
	"Bk": (97, 247, 247.070307),
	"Cf": (98, 251, 251.079587),
	"Es": (99, 252, 252.082980),
	"Fm": (100, 257, 257.095105),
	"Md": (101, 258, 258.098431),
	"No": (102, 259, 259.101030),
	"Lr": (103, 262, 262.109610),
	"Rf": (104, 267, 267.121790),
	"Db": (105, 268, 268.125670),
	"Sg": (106, 271, 271.133930),
	"Bh": (107, 272, 272.138260),
	"Hs": (108, 270, 270.134290),
	"Mt": (109, 276, 276.151590),
	"Ds": (110, 281, 281.164510),
	"Rg": (111, 280, 280.165140),
	"Cn": (112, 285, 285.177120),
	"Nh": (113, 284, 284.178730),
	"Fl": (114, 289, 289.190420),
	"Mc": (115, 288, 288.192740),
	"Lv": (116, 293, 293.204490),
	"Ts": (117, 292, 292.207460),
	"Og": (118, 294, 294.213920),
}

# Special isotope symbols that map to specific mass numbers
special_isotopes = {
	"D": (1, 2, 2.01410177812),
	"T": (1, 3, 3.0160492779),
}

# Create reverse lookup dictionary (using only standard isotopes)
default_from_number = {num: (sym, mass_num, mass) for sym, (num, mass_num, mass) in default_from_symbol.items()}

# Dictionary of exact masses for specific isotopes
# Keys are tuples of (symbol, mass_number)
isotope_data = {
	("H", 1): 1.00782503223,
	("H", 2): 2.01410177812,
	("H", 3): 3.0160492779,
	("D", 2): 2.01410177812,
	("T", 3): 3.0160492779,
	("He", 3): 3.0160293201,
	("He", 4): 4.00260325413,
	("Li", 6): 6.0151228874,
	("Li", 7): 7.0160034366,
	("Be", 9): 9.012183065,
	("B", 10): 10.0129369,
	("B", 11): 11.00930536,
	("C", 12): 12.0000000,
	("C", 13): 13.00335483507,
	("N", 14): 14.00307400443,
	("N", 15): 15.00010889888,
	("O", 16): 15.99491461957,
	("O", 17): 16.99913175650,
	("O", 18): 17.99915961286,
	("F", 19): 18.99840316273,
	("Ne", 20): 19.9924401762,
	("Ne", 21): 20.993846685,
	("Ne", 22): 21.991385114,
	("Na", 23): 22.9897692820,
	("Mg", 24): 23.985041697,
	("Mg", 25): 24.985836976,
	("Mg", 26): 25.982592968,
	("Al", 27): 26.98153853,
	("Si", 28): 27.97692653465,
	("Si", 29): 28.97649466490,
	("Si", 30): 29.973770136,
	("P", 31): 30.97376199842,
	("S", 32): 31.9720711744,
	("S", 33): 32.97145875870,
	("S", 34): 33.967867004,
	("S", 36): 35.96708071,
	("Cl", 35): 34.968852682,
	("Cl", 37): 36.965902602,
	("Ar", 36): 35.967545105,
	("Ar", 38): 37.96273211,
	("Ar", 40): 39.9623831237,
	("K", 39): 38.9637064864,
	("K", 40): 39.963998166,
	("K", 41): 40.9618252579,
	("Ca", 40): 39.962590863,
	("Ca", 42): 41.95861783,
	("Ca", 43): 42.95876644,
	("Ca", 44): 43.95548156,
	("Ca", 46): 45.9536890,
	("Ca", 48): 47.95252276,
	("Sc", 45): 44.95590828,
	("Ti", 46): 45.95262772,
	("Ti", 47): 46.95175879,
	("Ti", 48): 47.94794198,
	("Ti", 49): 48.94786568,
	("Ti", 50): 49.94478689,
	("V", 50): 49.94715601,
	("V", 51): 50.94395704,
	("Cr", 50): 49.94604183,
	("Cr", 52): 51.94050623,
	("Cr", 53): 52.94064815,
	("Cr", 54): 53.93887916,
	("Mn", 55): 54.93804391,
	("Fe", 54): 53.93960899,
	("Fe", 56): 55.93493633,
	("Fe", 57): 56.93539284,
	("Fe", 58): 57.93327443,
	("Co", 59): 58.93319429,
	("Ni", 58): 57.93534241,
	("Ni", 60): 59.93078588,
	("Ni", 61): 60.93105557,
	("Ni", 62): 61.92834537,
	("Ni", 64): 63.92796682,
	("Cu", 63): 62.92959772,
	("Cu", 65): 64.92778970,
	("Zn", 64): 63.92914201,
	("Zn", 66): 65.92603381,
	("Zn", 67): 66.92712775,
	("Zn", 68): 67.92484455,
	("Zn", 70): 69.92532310,
	("Ga", 69): 68.92558860,
	("Ga", 71): 70.92470258,
	("Ge", 70): 69.92424875,
	("Ge", 72): 71.92207583,
	("Ge", 73): 72.92345896,
	("Ge", 74): 73.92117776,
	("Ge", 76): 75.92140273,
	("As", 75): 74.92159457,
	("Se", 74): 73.92247593,
	("Se", 76): 75.91921378,
	("Se", 77): 76.91991415,
	("Se", 78): 77.91730928,
	("Se", 80): 79.91652128,
	("Se", 82): 81.91667033,
	("Br", 79): 78.91833710,
	("Br", 81): 80.91629056,
	("Kr", 78): 77.92036494,
	("Kr", 80): 79.91637808,
	("Kr", 82): 81.91348273,
	("Kr", 83): 82.91412716,
	("Kr", 84): 83.91149773,
	("Kr", 86): 85.91061063,
	("Rb", 85): 84.91178974,
	("Rb", 87): 86.90918053,
	("Sr", 84): 83.91342197,
	("Sr", 86): 85.90926073,
	("Sr", 87): 86.90887750,
	("Sr", 88): 87.90561226,
	("Y", 89): 88.90584830,
	("Zr", 90): 89.90470166,
	("Zr", 91): 90.90564299,
	("Zr", 92): 91.90503655,
	("Zr", 94): 93.90631412,
	("Zr", 96): 95.90827760,
	("Nb", 93): 92.90637806,
	("Mo", 92): 91.90680796,
	("Mo", 94): 93.90508490,
	("Mo", 95): 94.90583877,
	("Mo", 96): 95.90467612,
	("Mo", 97): 96.90601812,
	("Mo", 98): 97.90540482,
	("Mo", 100): 99.90747477,
	("Tc", 97): 96.90636526,
	("Tc", 98): 97.90721599,
	("Tc", 99): 98.90625475,
	("Ru", 96): 95.90759025,
	("Ru", 98): 97.90529954,
	("Ru", 99): 98.90593046,
	("Ru", 100): 99.90421628,
	("Ru", 101): 100.90557426,
	("Ru", 102): 101.90434930,
	("Ru", 104): 103.90543481,
	("Rh", 103): 102.90550393,
	("Pd", 102): 101.90563239,
	("Pd", 104): 103.90403235,
	("Pd", 105): 104.90508492,
	("Pd", 106): 105.90348764,
	("Pd", 108): 107.90389433,
	("Pd", 110): 109.90517220,
	("Ag", 107): 106.90509474,
	("Ag", 109): 108.90475628,
	("Cd", 106): 105.90645941,
	("Cd", 108): 107.90418157,
	("Cd", 110): 109.90300661,
	("Cd", 111): 110.90418287,
	("Cd", 112): 111.90276287,
	("Cd", 113): 112.90440813,
	("Cd", 114): 113.90336509,
	("Cd", 116): 115.90476315,
	("In", 113): 112.90406184,
	("In", 115): 114.90387877,
	("Sn", 112): 111.90482387,
	("Sn", 114): 113.90278099,
	("Sn", 115): 114.90334469,
	("Sn", 116): 115.90174280,
	("Sn", 117): 116.90295398,
	("Sn", 118): 117.90160657,
	("Sn", 119): 118.90331117,
	("Sn", 120): 119.90220163,
	("Sn", 122): 121.90343655,
	("Sb", 121): 120.90381639,
	("Sb", 123): 122.90421786,
	("Te", 120): 119.90402350,
	("Te", 122): 121.90304224,
	("Te", 123): 122.90427192,
	("Te", 124): 123.90281909,
	("Te", 125): 124.90442474,
	("Te", 126): 125.90331468,
	("Te", 128): 127.90446128,
	("Te", 130): 129.90622275,
	("I", 127): 126.90447280,
	("Xe", 124): 123.90589114,
	("Xe", 126): 125.90408660,
	("Xe", 128): 127.90353450,
	("Xe", 129): 128.90478086,
	("Xe", 130): 129.90350840,
	("Xe", 131): 130.90508406,
	("Xe", 132): 131.90415509,
	("Xe", 134): 133.90539466,
	("Xe", 136): 135.90721448,
	("Cs", 133): 132.90545196,
	("Ba", 130): 129.90632105,
	("Ba", 132): 131.90504130,
	("Ba", 134): 133.90449204,
	("Ba", 135): 134.90568838,
	("Ba", 136): 135.90457573,
	("Ba", 137): 136.90582714,
	("Ba", 138): 137.90524700,
	("La", 138): 137.90712300,
	("La", 139): 138.90635330,
	("Ce", 136): 135.90712921,
	("Ce", 138): 137.90599591,
	("Ce", 140): 139.90543870,
	("Ce", 142): 141.90924730,
	("Pr", 141): 140.90765931,
	("Nd", 142): 141.90772130,
	("Nd", 143): 142.90981720,
	("Nd", 144): 143.91008720,
	("Nd", 145): 144.91257930,
	("Nd", 146): 145.91311920,
	("Nd", 148): 147.91689770,
	("Nd", 150): 149.92089220,
	("Pm", 145): 144.91275590,
	("Sm", 144): 143.91199720,
	("Sm", 147): 146.91489230,
	("Sm", 148): 147.91482290,
	("Sm", 149): 148.91718740,
	("Sm", 150): 149.91727340,
	("Sm", 152): 151.91973240,
	("Sm", 154): 153.92221640,
	("Eu", 151): 150.91985630,
	("Eu", 153): 152.92123110,
	("Gd", 152): 151.91979540,
	("Gd", 154): 153.92086700,
	("Gd", 155): 154.92262120,
	("Gd", 156): 155.92212780,
	("Gd", 157): 156.92396850,
	("Gd", 158): 157.92410810,
	("Gd", 160): 159.92705810,
	("Tb", 159): 158.92534640,
	("Dy", 156): 155.92428310,
	("Dy", 158): 157.92440990,
	("Dy", 160): 159.92519530,
	("Dy", 161): 160.92693190,
	("Dy", 162): 161.92680180,
	("Dy", 163): 162.92873390,
	("Dy", 164): 163.92917480,
	("Ho", 165): 164.93032090,
	("Er", 162): 161.92877900,
	("Er", 164): 163.92920580,
	("Er", 166): 165.93029310,
	("Er", 167): 166.93204750,
	("Er", 168): 167.93237580,
	("Er", 170): 169.93546690,
	("Tm", 169): 168.93421790,
	("Yb", 168): 167.93389340,
	("Yb", 170): 169.93476630,
	("Yb", 171): 170.93632540,
	("Yb", 172): 171.93638590,
	("Yb", 173): 172.93821580,
	("Yb", 174): 173.93886310,
	("Yb", 176): 175.94256830,
	("Lu", 175): 174.94077180,
	("Lu", 176): 175.94268970,
	("Hf", 174): 173.94004040,
	("Hf", 176): 175.94140760,
	("Hf", 177): 176.94322760,
	("Hf", 178): 177.94370520,
	("Hf", 179): 178.94581810,
	("Hf", 180): 179.94655090,
	("Ta", 180): 179.94746340,
	("Ta", 181): 180.94799580,
	("W", 180): 179.94670790,
	("W", 182): 181.94820394,
	("W", 183): 182.95022275,
	("W", 184): 183.95093092,
	("W", 186): 185.95436093,
	("Re", 185): 184.95295980,
	("Re", 187): 186.95575205,
	("Os", 184): 183.95248990,
	("Os", 186): 185.95383710,
	("Os", 187): 186.95574840,
	("Os", 188): 187.95583810,
	("Os", 189): 188.95814740,
	("Os", 190): 189.95844880,
	("Os", 192): 191.96147970,
	("Ir", 191): 190.96059350,
	("Ir", 193): 192.96292640,
	("Pt", 190): 189.95993000,
	("Pt", 192): 191.96103400,
	("Pt", 194): 193.96267690,
	("Pt", 195): 194.96479110,
	("Pt", 196): 195.96495209,
	("Pt", 198): 197.96789620,
	("Au", 197): 196.96656879,
	("Hg", 196): 195.96583100,
	("Hg", 198): 197.96676860,
	("Hg", 199): 198.96828064,
	("Hg", 200): 199.96832659,
	("Hg", 201): 200.97030284,
	("Hg", 202): 201.97064340,
	("Hg", 204): 203.97349398,
	("Tl", 203): 202.97234422,
	("Tl", 205): 204.97442850,
	("Pb", 204): 203.97304100,
	("Pb", 206): 205.97444719,
	("Pb", 207): 206.97589731,
	("Pb", 208): 207.97665210,
	("Bi", 209): 208.98039860,
	("Po", 209): 208.98243040,
	("At", 210): 209.98714800,
	("Rn", 211): 210.99058700,
	("Fr", 223): 223.01973600,
	("Ra", 223): 223.01850300,
	("Ra", 224): 224.02021100,
	("Ra", 226): 226.02540980,
	("Ra", 228): 228.03107000,
	("Ac", 227): 227.02774700,
	("Th", 230): 230.03313400,
	("Th", 232): 232.03805500,
	("Pa", 231): 231.03588200,
	("U", 233): 233.03963400,
	("U", 234): 234.04095200,
	("U", 235): 235.04392800,
	("U", 236): 236.04556300,
	("U", 238): 238.05078600,
	("Np", 237): 237.04817300,
	("Pu", 238): 238.04955700,
	("Pu", 239): 239.05216300,
	("Pu", 240): 240.05381400,
	("Pu", 241): 241.05685100,
	("Pu", 242): 242.05874400,
	("Am", 241): 241.05682900,
	("Am", 243): 243.06138100,
	("Cm", 243): 243.06138100,
	("Cm", 244): 244.06275300,
	("Cm", 245): 245.06548600,
	("Cm", 246): 246.06721800,
	("Cm", 247): 247.07035300,
	("Cm", 248): 248.07234900,
	("Bk", 247): 247.07030700,
	("Bk", 249): 249.07498000,
	("Cf", 249): 249.07485000,
	("Cf", 250): 250.07640700,
	("Cf", 251): 251.07958700,
	("Cf", 252): 252.08162900,
	("Es", 252): 252.08298000,
	("Fm", 257): 257.09510500,
	("Md", 258): 258.09843100,
	("Md", 260): 260.10365000,
	("No", 259): 259.10103000,
	("Lr", 262): 262.10961000,
	("Rf", 267): 267.12179000,
	("Db", 268): 268.12567000,
	("Sg", 271): 271.13393000,
	("Bh", 272): 272.13826000,
	("Hs", 270): 270.13429000,
	("Mt", 276): 276.15159000,
	("Ds", 281): 281.16451000,
	("Rg", 280): 280.16514000,
	("Cn", 285): 285.17712000,
	("Nh", 284): 284.17873000,
	("Fl", 289): 289.19042000,
	("Mc", 288): 288.19274000,
	("Lv", 293): 293.20449000,
	("Ts", 292): 292.20746000,
	("Og", 294): 294.21392000,
}


class Atom:
	"""
	Class representing an atomic element with its physical properties.

	This class provides functionality to create and manipulate atomic data,
	including support for different isotopes and mass specifications.

	Attributes:
		symbol (str): Chemical symbol of the atom (e.g., 'H' for hydrogen)
		atomic_number (int): Number of protons in the nucleus
		mass_number (int): Total number of protons and neutrons, -1 if not applicable
		mass (float): Isotopic mass in atomic mass units (amu)
	"""

	__slots__ = ("_symbol", "_atomic_number", "_mass_number", "_mass")

	# Add class variables for data access
	default_from_symbol: ClassVar[Dict[str, Tuple[int, int, float]]] = {**default_from_symbol, **special_isotopes}
	default_from_number: ClassVar[Dict[int, Tuple[str, int, float]]] = default_from_number
	isotope_data: ClassVar[Dict[Tuple[str, int], float]] = isotope_data

	# Cache for title-cased symbols
	_symbol_cache: ClassVar[Dict[str, str]] = {}

	def __init__(self, symbol: str, atomic_number: int, mass_number: int, mass: float) -> None:
		"""Initialize an atom with its fundamental properties."""
		if atomic_number < 0:
			raise ValueError("Atomic number cannot be negative")
		if not symbol.strip():
			raise ValueError("Symbol cannot be empty")

		# Use cached title-cased symbol or create new one
		self._symbol = self._get_title_symbol(symbol)
		self._atomic_number = atomic_number
		self._mass_number = mass_number
		self._mass = float(mass)

	@classmethod
	def _get_title_symbol(cls, symbol: str) -> str:
		"""Get or create cached title-cased symbol."""
		if symbol not in cls._symbol_cache:
			cls._symbol_cache[symbol] = symbol.title()
		return cls._symbol_cache[symbol]

	@property
	def symbol(self) -> str:
		"""Chemical symbol of the atom."""
		return self._symbol

	@property
	def atomic_number(self) -> int:
		"""Number of protons in the nucleus."""
		return self._atomic_number

	@property
	def mass_number(self) -> int:
		"""Total number of protons and neutrons."""
		return self._mass_number

	@mass_number.setter
	def mass_number(self, value: int) -> None:
		self._mass_number = value

	@property
	def mass(self) -> float:
		"""Isotopic mass in atomic mass units."""
		return self._mass

	@mass.setter
	def mass(self, value: float) -> None:
		self._mass = float(value)

	@classmethod
	def from_symbol_mass_number(cls, symbol: str, mass_number: int) -> "Atom":
		"""
		Construct atom from symbol and mass number.

		Args:
			symbol: Chemical symbol of the atom
			mass_number: Mass number of the isotope

		Returns:
			Atom: New atom instance with properties of the specified isotope
		"""
		titled_symbol = cls._get_title_symbol(symbol)
		atomic_number = cls.default_from_symbol[titled_symbol][0]

		# Try to get mass from isotope data, fall back to default if not found
		try:
			mass = cls.isotope_data[(titled_symbol, mass_number)]
		except KeyError:
			# Use default mass if isotope not found
			_, default_mass_number, mass = cls.default_from_symbol[titled_symbol]
			mass_number = default_mass_number

		return cls(titled_symbol, atomic_number, mass_number, mass)

	@classmethod
	def from_symbol(cls, symbol: str) -> "Atom":
		"""
		Construct atom from symbol using most abundant isotope data.

		Args:
			symbol: Chemical symbol of the atom

		Returns:
			Atom: New atom instance with properties of the most abundant isotope
		"""
		titled_symbol = cls._get_title_symbol(symbol)
		atomic_number, mass_number, mass = cls.default_from_symbol[titled_symbol]
		return cls(titled_symbol, atomic_number, mass_number, mass)

	@classmethod
	def from_atomic_number(cls, atomic_number: int) -> "Atom":
		"""
		Construct atom from atomic number using most abundant isotope.

		Args:
			atomic_number: Number of protons in the nucleus

		Returns:
			Atom: New atom instance with properties of the most abundant isotope
		"""
		symbol, mass_number, mass = cls.default_from_number[atomic_number]
		return cls(symbol, atomic_number, mass_number, mass)

	def change_mass(self, mass_string: Union[str, float, int]) -> None:
		"""
		Update the mass and mass number of the atom.

		Args:
			mass_string: New mass value. Can be:
				- A string with decimal point for exact mass
				- An integer or string without decimal for mass number
				- A float for exact mass

		If given a mass number, tries to find the corresponding exact mass
		from isotope_data. If not found, uses the mass number as the mass.
		"""
		if isinstance(mass_string, (int, float)):
			mass_str = str(mass_string)
		else:
			mass_str = mass_string

		if "." in mass_str:
			self.mass = float(mass_str)
			self.mass_number = round(self.mass)
		else:
			mass_num = int(mass_str)
			try:
				self.mass = self.isotope_data[(self.symbol, mass_num)]
				self.mass_number = mass_num
			except KeyError:
				self.mass_number = mass_num
				self.mass = float(mass_num)

	def __str__(self) -> str:
		"""Return string representation."""
		return f"{self._symbol:2} {self._mass:11.7f} amu"

	def __repr__(self) -> str:
		"""
		Return a detailed string representation of the atom.

		Returns:
			str: String containing all atom properties
		"""
		return (
			f"Atom(symbol='{self._symbol}', atomic_number={self._atomic_number}, "
			f"mass_number={self._mass_number}, mass={self._mass})"
		)
