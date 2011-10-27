CREATE TABLE nfe_city_data (
    id bigserial NOT NULL PRIMARY KEY,
    state_code integer,
    state_name text,
    city_code integer,
    city_name text);

COPY nfe_city_data (state_code, state_name, city_code, city_name) FROM stdin;
11	Rondonia	1100148	Nova Brasilandia D'Oeste
11	Rondonia	1100320	Sao Miguel do Guapore
11	Rondonia	1100346	Alvorada D'Oeste
11	Rondonia	1101500	Seringueiras
11	Rondonia	1100015	Alta Floresta D'Oeste
11	Rondonia	1100049	Cacoal
11	Rondonia	1100098	Espigao D'Oeste
11	Rondonia	1100288	Rolim de Moura
11	Rondonia	1100296	Santa Luzia D'Oeste
11	Rondonia	1100379	Alto Alegre dos Parecis
11	Rondonia	1100502	Novo Horizonte do Oeste
11	Rondonia	1100908	Castanheiras
11	Rondonia	1101203	Ministro Andreazza
11	Rondonia	1100189	Pimenta Bueno
11	Rondonia	1100304	Vilhena
11	Rondonia	1100924	Chupinguaia
11	Rondonia	1101450	Parecis
11	Rondonia	1101476	Primavera de Rondonia
11	Rondonia	1101484	Sao Felipe D'Oeste
11	Rondonia	1100031	Cabixi
11	Rondonia	1100056	Cerejeiras
11	Rondonia	1100064	Colorado do Oeste
11	Rondonia	1100072	Corumbiara
11	Rondonia	1101468	Pimenteiras do Oeste
12	Acre	1200203	Cruzeiro do Sul
12	Acre	1200336	Mancio Lima
12	Acre	1200351	Marechal Thaumaturgo
12	Acre	1200393	Porto Walter
12	Acre	1200427	Rodrigues Alves
12	Acre	1200302	Feijo
12	Acre	1200328	Jordao
12	Acre	1200609	Tarauaca
12	Acre	1200344	Manoel Urbano
12	Acre	1200435	Santa Rosa do Purus
12	Acre	1200500	Sena Madureira
12	Acre	1200013	Acrelandia
12	Acre	1200138	Bujari
12	Acre	1200179	Capixaba
12	Acre	1200385	Placido de Castro
12	Acre	1200401	Rio Branco
12	Acre	1200450	Senador Guiomard
12	Acre	1200807	Porto Acre
12	Acre	1200054	Assis Brasil
12	Acre	1200104	Brasileia
12	Acre	1200252	Epitaciolandia
12	Acre	1200708	Xapuri
13	Amazonas	1300409	Barcelos
13	Amazonas	1303205	Novo Airao
11	Rondonia	1100205	Porto Velho
11	Rondonia	1100338	Nova Mamore
11	Rondonia	1100452	Buritis
11	Rondonia	1100700	Campo Novo de Rondonia
11	Rondonia	1100809	Candeias do Jamari
11	Rondonia	1100940	Cujubim
11	Rondonia	1101104	Itapua do Oeste
11	Rondonia	1100080	Costa Marques
11	Rondonia	1100106	Guajara-Mirim
11	Rondonia	1101492	Sao Francisco do Guapore
11	Rondonia	1100023	Ariquemes
11	Rondonia	1100130	Machadinho D'Oeste
11	Rondonia	1100262	Rio Crespo
11	Rondonia	1100403	Alto Paraiso
11	Rondonia	1100601	Cacaulandia
11	Rondonia	1101401	Monte Negro
11	Rondonia	1101757	Vale do Anari
11	Rondonia	1100114	Jaru
11	Rondonia	1100122	Ji-Parana
11	Rondonia	1100155	Ouro Preto do Oeste
11	Rondonia	1100254	Presidente Medici
11	Rondonia	1101005	Governador Jorge Teixeira
11	Rondonia	1101302	Mirante da Serra
11	Rondonia	1101435	Nova Uniao
11	Rondonia	1101559	Teixeiropolis
11	Rondonia	1101609	Theobroma
11	Rondonia	1101708	Urupa
11	Rondonia	1101807	Vale do Paraiso
13	Amazonas	1303601	Santa Isabel do Rio Negro
13	Amazonas	1303809	Sao Gabriel da Cachoeira
13	Amazonas	1302108	Japura
13	Amazonas	1302801	Maraa
13	Amazonas	1300060	Amatura
13	Amazonas	1300201	Atalaia do Norte
13	Amazonas	1300607	Benjamin Constant
13	Amazonas	1301605	Fonte Boa
13	Amazonas	1302306	Jutai
13	Amazonas	1303700	Santo Antonio do Ica
13	Amazonas	1303908	Sao Paulo de Olivenca
13	Amazonas	1304062	Tabatinga
13	Amazonas	1304237	Tonantins
13	Amazonas	1301001	Carauari
13	Amazonas	1301407	Eirunepe
13	Amazonas	1301506	Envira
13	Amazonas	1301654	Guajara
13	Amazonas	1301803	Ipixuna
13	Amazonas	1301951	Itamarati
13	Amazonas	1302207	Jurua
13	Amazonas	1300029	Alvaraes
13	Amazonas	1304203	Tefe
13	Amazonas	1304260	Uarini
13	Amazonas	1300086	Anama
13	Amazonas	1300102	Anori
13	Amazonas	1300631	Beruri
13	Amazonas	1300839	Caapiranga
13	Amazonas	1301209	Coari
13	Amazonas	1301308	Codajas
13	Amazonas	1300300	Autazes
13	Amazonas	1301100	Careiro
13	Amazonas	1301159	Careiro da Varzea
13	Amazonas	1301852	Iranduba
13	Amazonas	1302504	Manacapuru
13	Amazonas	1302553	Manaquiri
13	Amazonas	1302603	Manaus
13	Amazonas	1303536	Presidente Figueiredo
13	Amazonas	1303569	Rio Preto da Eva
13	Amazonas	1301902	Itacoatiara
13	Amazonas	1302009	Itapiranga
13	Amazonas	1303106	Nova Olinda do Norte
13	Amazonas	1304005	Silves
13	Amazonas	1304401	Urucurituba
13	Amazonas	1300508	Barreirinha
13	Amazonas	1300680	Boa Vista do Ramos
13	Amazonas	1302900	Maues
13	Amazonas	1303007	Nhamunda
13	Amazonas	1303403	Parintins
13	Amazonas	1303957	Sao Sebastiao do Uatuma
13	Amazonas	1304302	Urucara
13	Amazonas	1300706	Boca do Acre
13	Amazonas	1303502	Pauini
13	Amazonas	1300904	Canutama
13	Amazonas	1302405	Labrea
13	Amazonas	1304104	Tapaua
13	Amazonas	1300144	Apui
13	Amazonas	1300805	Borba
13	Amazonas	1301704	Humaita
13	Amazonas	1302702	Manicore
13	Amazonas	1303304	Novo Aripuana
14	Roraima	1400027	Amajari
14	Roraima	1400050	Alto Alegre
14	Roraima	1400100	Boa Vista
14	Roraima	1400456	Pacaraima
14	Roraima	1400159	Bonfim
14	Roraima	1400175	Canta
14	Roraima	1400407	Normandia
14	Roraima	1400704	Uiramuta
14	Roraima	1400209	Caracarai
14	Roraima	1400282	Iracema
14	Roraima	1400308	Mucajai
14	Roraima	1400233	Caroebe
14	Roraima	1400472	Rorainopolis
14	Roraima	1400506	Sao Joao da Baliza
14	Roraima	1400605	Sao Luiz
15	Para	1503002	Faro
15	Para	1503903	Juruti
15	Para	1505106	obidos
15	Para	1505304	Oriximina
15	Para	1507979	Terra Santa
15	Para	1500404	Alenquer
15	Para	1501451	Belterra
15	Para	1502855	Curua
15	Para	1504802	Monte Alegre
15	Para	1505650	Placas
15	Para	1506005	Prainha
15	Para	1506807	Santarem
15	Para	1500503	Almeirim
15	Para	1505908	Porto de Moz
15	Para	1501105	Bagre
15	Para	1503101	Gurupa
15	Para	1504505	Melgaco
15	Para	1505809	Portel
15	Para	1500305	Afua
15	Para	1500701	Anajas
15	Para	1501808	Breves
15	Para	1502806	Curralinho
15	Para	1507706	Sao Sebastiao da Boa Vista
15	Para	1502004	Cachoeira do Arari
15	Para	1502509	Chaves
15	Para	1504901	Muana
15	Para	1505700	Ponta de Pedras
15	Para	1506302	Salvaterra
15	Para	1506401	Santa Cruz do Arari
15	Para	1507904	Soure
15	Para	1500800	Ananindeua
15	Para	1501303	Barcarena
15	Para	1501402	Belem
15	Para	1501501	Benevides
15	Para	1504422	Marituba
15	Para	1506351	Santa Barbara do Para
15	Para	1501907	Bujaru
15	Para	1502400	Castanhal
15	Para	1503408	Inhangapi
15	Para	1506500	Santa Isabel do Para
15	Para	1507003	Santo Antonio do Taua
15	Para	1502608	Colares
15	Para	1502905	Curuca
15	Para	1504109	Magalhaes Barata
15	Para	1504307	Maracana
15	Para	1504406	Marapanim
15	Para	1506203	Salinopolis
15	Para	1507102	Sao Caetano de Odivelas
15	Para	1507466	Sao Joao da Ponta
15	Para	1507474	Sao Joao de Pirabas
15	Para	1507961	Terra Alta
15	Para	1508209	Vigia
15	Para	1500909	Augusto Correa
15	Para	1501600	Bonito
15	Para	1501709	Braganca
15	Para	1502202	Capanema
15	Para	1503200	Igarape-Acu
15	Para	1505007	Nova Timboteua
15	Para	1505601	Peixe-Boi
15	Para	1506104	Primavera
15	Para	1506112	Quatipuru
15	Para	1506609	Santa Maria do Para
15	Para	1506906	Santarem Novo
15	Para	1507409	Sao Francisco do Para
15	Para	1508035	Tracuateua
15	Para	1500107	Abaetetuba
15	Para	1501204	Baiao
15	Para	1502103	Cameta
15	Para	1503309	Igarape-Miri
15	Para	1504000	Limoeiro do Ajuru
15	Para	1504604	Mocajuba
15	Para	1505205	Oeiras do Para
15	Para	1500206	Acara
15	Para	1502756	Concordia do Para
15	Para	1504703	Moju
15	Para	1507953	Tailandia
15	Para	1508001	Tome-Acu
15	Para	1500958	Aurora do Para
15	Para	1501956	Cachoeira do Piria
15	Para	1502301	Capitao Poco
15	Para	1503077	Garrafao do Norte
15	Para	1503457	Ipixuna do Para
15	Para	1503507	Irituia
15	Para	1504059	Mae do Rio
15	Para	1504950	Nova Esperanca do Piria
15	Para	1505403	Ourem
15	Para	1506559	Santa Luzia do Para
15	Para	1507201	Sao Domingos do Capim
15	Para	1507607	Sao Miguel do Guama
15	Para	1508308	Viseu
15	Para	1501006	Aveiro
15	Para	1503606	Itaituba
15	Para	1503754	Jacareacanga
15	Para	1505031	Novo Progresso
15	Para	1506195	Ruropolis
15	Para	1508050	Trairao
15	Para	1500602	Altamira
15	Para	1500859	Anapu
15	Para	1501725	Brasil Novo
15	Para	1504455	Medicilandia
15	Para	1505486	Pacaja
15	Para	1507805	Senador Jose Porfirio
15	Para	1508159	Uruara
15	Para	1508357	Vitoria do Xingu
15	Para	1501782	Breu Branco
15	Para	1503705	Itupiranga
15	Para	1503804	Jacunda
15	Para	1504976	Nova Ipixuna
15	Para	1505064	Novo Repartimento
15	Para	1508100	Tucurui
15	Para	1500131	Abel Figueiredo
15	Para	1501576	Bom Jesus do Tocantins
15	Para	1502939	Dom Eliseu
15	Para	1503093	Goianesia do Para
15	Para	1505502	Paragominas
15	Para	1506187	Rondon do Para
15	Para	1508126	Ulianopolis
15	Para	1501253	Bannach
15	Para	1502764	Cumaru do Norte
15	Para	1505437	Ourilandia do Norte
15	Para	1507300	Sao Felix do Xingu
15	Para	1508084	Tucuma
15	Para	1500347	agua Azul do Norte
15	Para	1502152	Canaa dos Carajas
15	Para	1502772	Curionopolis
15	Para	1502954	Eldorado dos Carajas
15	Para	1505536	Parauapebas
15	Para	1501758	Brejo Grande do Araguaia
15	Para	1504208	Maraba
15	Para	1505494	Palestina do Para
15	Para	1507151	Sao Domingos do Araguaia
15	Para	1507508	Sao Joao do Araguaia
15	Para	1505551	Pau D'Arco
15	Para	1505635	Picarra
15	Para	1506138	Redencao
15	Para	1506161	Rio Maria
15	Para	1507458	Sao Geraldo do Araguaia
15	Para	1507755	Sapucaia
15	Para	1508407	Xinguara
15	Para	1502707	Conceicao do Araguaia
15	Para	1503044	Floresta do Araguaia
15	Para	1506583	Santa Maria das Barreiras
15	Para	1506708	Santana do Araguaia
16	Amapa	1600204	Calcoene
16	Amapa	1600501	Oiapoque
16	Amapa	1600105	Amapa
16	Amapa	1600550	Pracuuba
16	Amapa	1600709	Tartarugalzinho
16	Amapa	1600055	Serra do Navio
16	Amapa	1600154	Pedra Branca do Amapari
16	Amapa	1600212	Cutias
16	Amapa	1600238	Ferreira Gomes
16	Amapa	1600253	Itaubal
16	Amapa	1600303	Macapa
16	Amapa	1600535	Porto Grande
16	Amapa	1600600	Santana
16	Amapa	1600279	Laranjal do Jari
16	Amapa	1600402	Mazagao
16	Amapa	1600808	Vitoria do Jari
17	Tocantins	1700301	Aguiarnopolis
17	Tocantins	1701002	Ananas
17	Tocantins	1701051	Angico
17	Tocantins	1702208	Araguatins
17	Tocantins	1702554	Augustinopolis
17	Tocantins	1702901	Axixa do Tocantins
17	Tocantins	1703800	Buriti do Tocantins
17	Tocantins	1703826	Cachoeirinha
17	Tocantins	1703891	Carrasco Bonito
17	Tocantins	1706506	Darcinopolis
17	Tocantins	1707405	Esperantina
17	Tocantins	1710706	Itaguatins
17	Tocantins	1712454	Luzinopolis
17	Tocantins	1712801	Maurilandia do Tocantins
17	Tocantins	1713809	Palmeiras do Tocantins
17	Tocantins	1714302	Nazare
17	Tocantins	1718303	Praia Norte
17	Tocantins	1718550	Riachinho
17	Tocantins	1718808	Sampaio
17	Tocantins	1720002	Santa Terezinha do Tocantins
17	Tocantins	1720101	Sao Bento do Tocantins
17	Tocantins	1720200	Sao Miguel do Tocantins
17	Tocantins	1720309	Sao Sebastiao do Tocantins
17	Tocantins	1720804	Sitio Novo do Tocantins
17	Tocantins	1721208	Tocantinopolis
17	Tocantins	1701309	Aragominas
17	Tocantins	1702109	Araguaina
17	Tocantins	1702158	Araguana
17	Tocantins	1702307	Arapoema
17	Tocantins	1703008	Babaculandia
17	Tocantins	1703057	Bandeirantes do Tocantins
17	Tocantins	1703883	Carmolandia
17	Tocantins	1705508	Colinas do Tocantins
17	Tocantins	1707702	Filadelfia
17	Tocantins	1713957	Muricilandia
17	Tocantins	1714880	Nova Olinda
17	Tocantins	1715705	Palmeirante
17	Tocantins	1716307	Pau D'Arco
17	Tocantins	1717206	Piraque
17	Tocantins	1718865	Santa Fe do Araguaia
17	Tocantins	1722081	Wanderlandia
17	Tocantins	1722107	Xambioa
17	Tocantins	1700251	Abreulandia
17	Tocantins	1701903	Araguacema
17	Tocantins	1703107	Barrolandia
17	Tocantins	1703206	Bernardo Sayao
17	Tocantins	1703602	Brasilandia do Tocantins
17	Tocantins	1703909	Caseara
17	Tocantins	1706001	Couto de Magalhaes
17	Tocantins	1707108	Divinopolis do Tocantins
17	Tocantins	1707207	Dois Irmaos do Tocantins
17	Tocantins	1708254	Fortaleza do Tabocao
17	Tocantins	1708304	Goianorte
17	Tocantins	1709302	Guarai
17	Tocantins	1711100	Itapora do Tocantins
17	Tocantins	1711803	Juarina
17	Tocantins	1712504	Marianopolis do Tocantins
17	Tocantins	1713205	Miracema do Tocantins
17	Tocantins	1713304	Miranorte
17	Tocantins	1713700	Monte Santo do Tocantins
17	Tocantins	1716653	Pequizeiro
17	Tocantins	1716703	Colmeia
17	Tocantins	1718402	Presidente Kennedy
17	Tocantins	1718709	Rio dos Bois
17	Tocantins	1721257	Tupirama
17	Tocantins	1721307	Tupiratins
17	Tocantins	1702000	Araguacu
17	Tocantins	1704600	Chapada de Areia
17	Tocantins	1706100	Cristalandia
17	Tocantins	1707306	Duere
17	Tocantins	1707553	Fatima
17	Tocantins	1708205	Formoso do Araguaia
17	Tocantins	1711902	Lagoa da Confusao
17	Tocantins	1715002	Nova Rosalandia
17	Tocantins	1715507	Oliveira de Fatima
17	Tocantins	1716109	Paraiso do Tocantins
17	Tocantins	1717503	Pium
17	Tocantins	1718451	Pugmil
17	Tocantins	1718840	Sandolandia
17	Tocantins	1700350	Alianca do Tocantins
17	Tocantins	1700707	Alvorada
17	Tocantins	1703701	Brejinho de Nazare
17	Tocantins	1703867	Cariri do Tocantins
17	Tocantins	1706258	Crixas do Tocantins
17	Tocantins	1707652	Figueiropolis
17	Tocantins	1709500	Gurupi
17	Tocantins	1711506	Jau do Tocantins
17	Tocantins	1715754	Palmeiropolis
17	Tocantins	1716604	Peixe
17	Tocantins	1718899	Santa Rita do Tocantins
17	Tocantins	1720259	Sao Salvador do Tocantins
17	Tocantins	1720853	Sucupira
17	Tocantins	1720978	Talisma
17	Tocantins	1701101	Aparecida do Rio Negro
17	Tocantins	1703305	Bom Jesus do Tocantins
17	Tocantins	1709807	Ipueiras
17	Tocantins	1712009	Lajeado
17	Tocantins	1713601	Monte do Carmo
17	Tocantins	1716505	Pedro Afonso
17	Tocantins	1718204	Porto Nacional
17	Tocantins	1718881	Santa Maria do Tocantins
17	Tocantins	1720655	Silvanopolis
17	Tocantins	1721000	Palmas
17	Tocantins	1721109	Tocantinia
17	Tocantins	1703073	Barra do Ouro
17	Tocantins	1703842	Campos Lindos
17	Tocantins	1704105	Centenario
17	Tocantins	1709005	Goiatins
17	Tocantins	1710508	Itacaja
17	Tocantins	1710904	Itapiratins
17	Tocantins	1711951	Lagoa do Tocantins
17	Tocantins	1712405	Lizarda
17	Tocantins	1712702	Mateiros
17	Tocantins	1715101	Novo Acordo
17	Tocantins	1717909	Ponte Alta do Tocantins
17	Tocantins	1718501	Recursolandia
17	Tocantins	1718758	Rio Sono
17	Tocantins	1719004	Santa Tereza do Tocantins
17	Tocantins	1720150	Sao Felix do Tocantins
17	Tocantins	1700400	Almas
17	Tocantins	1702406	Arraias
17	Tocantins	1702703	Aurora do Tocantins
17	Tocantins	1705102	Chapada da Natividade
17	Tocantins	1705557	Combinado
17	Tocantins	1705607	Conceicao do Tocantins
17	Tocantins	1707009	Dianopolis
17	Tocantins	1712157	Lavandeira
17	Tocantins	1714203	Natividade
17	Tocantins	1715150	Novo Alegre
17	Tocantins	1715259	Novo Jardim
17	Tocantins	1716208	Parana
17	Tocantins	1717008	Pindorama do Tocantins
17	Tocantins	1717800	Ponte Alta do Bom Jesus
17	Tocantins	1718006	Porto Alegre do Tocantins
17	Tocantins	1718659	Rio da Conceicao
17	Tocantins	1718907	Santa Rosa do Tocantins
17	Tocantins	1720499	Sao Valerio da Natividade
17	Tocantins	1720903	Taguatinga
17	Tocantins	1720937	Taipas do Tocantins
21	Maranhao	2100204	Alcantara
21	Maranhao	2100832	Apicum-Acu
21	Maranhao	2101301	Bacuri
21	Maranhao	2101350	Bacurituba
21	Maranhao	2101905	Bequimao
21	Maranhao	2102408	Cajapio
21	Maranhao	2103109	Cedral
21	Maranhao	2103125	Central do Maranhao
21	Maranhao	2103703	Cururupu
21	Maranhao	2104909	Guimaraes
21	Maranhao	2106805	Mirinzal
21	Maranhao	2109056	Porto Rico do Maranhao
21	Maranhao	2111789	Serrano do Maranhao
21	Maranhao	2107506	Paco do Lumiar
21	Maranhao	2109452	Raposa
21	Maranhao	2111201	Sao Jose de Ribamar
21	Maranhao	2111300	Sao Luis
21	Maranhao	2101103	Axixa
21	Maranhao	2101251	Bacabeira
21	Maranhao	2102374	Cachoeira Grande
21	Maranhao	2105104	Icatu
21	Maranhao	2107100	Morros
21	Maranhao	2109205	Presidente Juscelino
21	Maranhao	2109601	Rosario
21	Maranhao	2110203	Santa Rita
21	Maranhao	2101707	Barreirinhas
21	Maranhao	2105005	Humberto de Campos
21	Maranhao	2108058	Paulino Neves
21	Maranhao	2109403	Primeira Cruz
21	Maranhao	2110278	Santo Amaro do Maranhao
21	Maranhao	2112506	Tutoia
21	Maranhao	2100709	Anajatuba
21	Maranhao	2101004	Arari
21	Maranhao	2101772	Bela Vista do Maranhao
21	Maranhao	2102507	Cajari
21	Maranhao	2103554	Conceicao do Lago-Acu
21	Maranhao	2105153	Igarape do Meio
21	Maranhao	2106508	Matinha
21	Maranhao	2106904	Moncao
21	Maranhao	2107456	Olinda Nova do Maranhao
21	Maranhao	2107605	Palmeirandia
21	Maranhao	2108256	Pedro do Rosario
21	Maranhao	2108306	Penalva
21	Maranhao	2108405	Peri Mirim
21	Maranhao	2108603	Pinheiro
21	Maranhao	2109270	Presidente Sarney
21	Maranhao	2109809	Santa Helena
21	Maranhao	2110500	Sao Bento
21	Maranhao	2111003	Sao Joao Batista
21	Maranhao	2111706	Sao Vicente Ferrer
21	Maranhao	2112803	Viana
21	Maranhao	2112902	Vitoria do Mearim
21	Maranhao	2102705	Cantanhede
21	Maranhao	2105401	Itapecuru Mirim
21	Maranhao	2106631	Matoes do Norte
21	Maranhao	2106755	Miranda do Norte
21	Maranhao	2107209	Nina Rodrigues
21	Maranhao	2108801	Pirapemas
21	Maranhao	2109304	Presidente Vargas
21	Maranhao	2112704	Vargem Grande
21	Maranhao	2100550	Amapa do Maranhao
21	Maranhao	2101970	Boa Vista do Gurupi
21	Maranhao	2102606	Candido Mendes
21	Maranhao	2102903	Carutapera
21	Maranhao	2103158	Centro do Guilherme
21	Maranhao	2103174	Centro Novo do Maranhao
21	Maranhao	2104305	Godofredo Viana
21	Maranhao	2104677	Governador Nunes Freire
21	Maranhao	2105658	Junco do Maranhao
21	Maranhao	2106201	Luis Domingues
21	Maranhao	2106326	Maracacume
21	Maranhao	2106375	Maranhaozinho
21	Maranhao	2112407	Turiacu
21	Maranhao	2112456	Turilandia
21	Maranhao	2100402	Altamira do Maranhao
21	Maranhao	2100477	Alto Alegre do Pindare
21	Maranhao	2100873	Araguana
21	Maranhao	2102002	Bom Jardim
21	Maranhao	2102036	Bom Jesus das Selvas
21	Maranhao	2102150	Brejo de Areia
21	Maranhao	2102325	Buriticupu
21	Maranhao	2104651	Governador Newton Bello
21	Maranhao	2105708	Lago da Pedra
21	Maranhao	2105963	Lagoa Grande do Maranhao
21	Maranhao	2106359	Maraja do Sena
21	Maranhao	2107357	Nova Olinda do Maranhao
21	Maranhao	2108108	Paulo Ramos
21	Maranhao	2108504	Pindare-Mirim
21	Maranhao	2109239	Presidente Medici
21	Maranhao	2109908	Santa Ines
21	Maranhao	2110005	Santa Luzia
21	Maranhao	2110039	Santa Luzia do Parua
21	Maranhao	2111029	Sao Joao do Caru
21	Maranhao	2112274	Tufilandia
21	Maranhao	2113009	Vitorino Freire
21	Maranhao	2114007	Ze Doca
21	Maranhao	2100055	Acailandia
21	Maranhao	2100600	Amarante do Maranhao
21	Maranhao	2102358	Buritirana
21	Maranhao	2103257	Cidelandia
21	Maranhao	2103752	Davinopolis
21	Maranhao	2104552	Governador Edison Lobao
21	Maranhao	2105302	Imperatriz
21	Maranhao	2105427	Itinga do Maranhao
21	Maranhao	2105500	Joao Lisboa
21	Maranhao	2105989	Lajeado Novo
21	Maranhao	2107001	Montes Altos
21	Maranhao	2109551	Ribamar Fiquene
21	Maranhao	2110856	Sao Francisco do Brejao
21	Maranhao	2111532	Sao Pedro da agua Branca
21	Maranhao	2111763	Senador La Rocque
21	Maranhao	2112852	Vila Nova dos Martirios
21	Maranhao	2101202	Bacabal
21	Maranhao	2101939	Bernardo do Mearim
21	Maranhao	2102077	Bom Lugar
21	Maranhao	2104008	Esperantinopolis
21	Maranhao	2105203	Igarape Grande
21	Maranhao	2105807	Lago do Junco
21	Maranhao	2105906	Lago Verde
21	Maranhao	2105948	Lago dos Rodrigues
21	Maranhao	2106003	Lima Campos
21	Maranhao	2107407	Olho d'agua das Cunhas
21	Maranhao	2108207	Pedreiras
21	Maranhao	2108702	Pio XII
21	Maranhao	2108900	Pocao de Pedras
21	Maranhao	2110302	Santo Antonio dos Lopes
21	Maranhao	2111409	Sao Luis Gonzaga do Maranhao
21	Maranhao	2111508	Sao Mateus do Maranhao
21	Maranhao	2111631	Sao Raimundo do Doca Bezerra
21	Maranhao	2111672	Sao Roberto
21	Maranhao	2111722	Satubinha
21	Maranhao	2112233	Trizidela do Vale
21	Maranhao	2100956	Arame
21	Maranhao	2101608	Barra do Corda
21	Maranhao	2104081	Fernando Falcao
21	Maranhao	2104099	Formosa da Serra Negra
21	Maranhao	2104800	Grajau
21	Maranhao	2105351	Itaipava do Grajau
21	Maranhao	2105476	Jenipapo dos Vieiras
21	Maranhao	2105609	Joselandia
21	Maranhao	2109759	Santa Filomena do Maranhao
21	Maranhao	2111805	Sitio Novo
21	Maranhao	2112308	Tuntum
21	Maranhao	2103802	Dom Pedro
21	Maranhao	2104206	Fortuna
21	Maranhao	2104404	Goncalves Dias
21	Maranhao	2104503	Governador Archer
21	Maranhao	2104602	Governador Eugenio Barros
21	Maranhao	2104628	Governador Luiz Rocha
21	Maranhao	2104701	Graca Aranha
21	Maranhao	2109106	Presidente Dutra
21	Maranhao	2110708	Sao Domingos do Maranhao
21	Maranhao	2111250	Sao Jose dos Basilios
21	Maranhao	2111748	Senador Alexandre Costa
21	Maranhao	2100154	agua Doce do Maranhao
21	Maranhao	2100907	Araioses
21	Maranhao	2106300	Magalhaes de Almeida
21	Maranhao	2110104	Santa Quiteria do Maranhao
21	Maranhao	2110237	Santana do Maranhao
21	Maranhao	2110609	Sao Bernardo
21	Maranhao	2100808	Anapurus
21	Maranhao	2101731	Belagua
21	Maranhao	2102101	Brejo
21	Maranhao	2102200	Buriti
21	Maranhao	2103208	Chapadinha
21	Maranhao	2106409	Mata Roma
21	Maranhao	2106672	Milagres do Maranhao
21	Maranhao	2110401	Sao Benedito do Rio Preto
21	Maranhao	2112605	Urbano Santos
21	Maranhao	2100436	Alto Alegre do Maranhao
21	Maranhao	2102754	Capinzal do Norte
21	Maranhao	2103307	Codo
21	Maranhao	2103604	Coroata
21	Maranhao	2108454	Peritoro
21	Maranhao	2112100	Timbiras
21	Maranhao	2100105	Afonso Cunha
21	Maranhao	2100303	Aldeias Altas
21	Maranhao	2103406	Coelho Neto
21	Maranhao	2103901	Duque Bacelar
21	Maranhao	2102309	Buriti Bravo
21	Maranhao	2103000	Caxias
21	Maranhao	2106607	Matoes
21	Maranhao	2107803	Parnarama
21	Maranhao	2111078	Sao Joao do Soter
21	Maranhao	2112209	Timon
21	Maranhao	2101509	Barao de Grajau
21	Maranhao	2103505	Colinas
21	Maranhao	2105450	Jatoba
21	Maranhao	2105922	Lagoa do Mato
21	Maranhao	2106706	Mirador
21	Maranhao	2107308	Nova Iorque
21	Maranhao	2107704	Paraibano
21	Maranhao	2107902	Passagem Franca
21	Maranhao	2108009	Pastos Bons
21	Maranhao	2110906	Sao Francisco do Maranhao
21	Maranhao	2111102	Sao Joao dos Patos
21	Maranhao	2111904	Sucupira do Norte
21	Maranhao	2111953	Sucupira do Riachao
21	Maranhao	2102556	Campestre do Maranhao
21	Maranhao	2102804	Carolina
21	Maranhao	2104057	Estreito
21	Maranhao	2109007	Porto Franco
21	Maranhao	2111052	Sao Joao do Paraiso
21	Maranhao	2111573	Sao Pedro dos Crentes
21	Maranhao	2100501	Alto Parnaiba
21	Maranhao	2101400	Balsas
21	Maranhao	2104073	Feira Nova do Maranhao
21	Maranhao	2109502	Riachao
21	Maranhao	2112001	Tasso Fragoso
21	Maranhao	2101806	Benedito Leite
21	Maranhao	2104107	Fortaleza dos Nogueiras
21	Maranhao	2106102	Loreto
21	Maranhao	2107258	Nova Colinas
21	Maranhao	2109700	Sambaiba
21	Maranhao	2110658	Sao Domingos do Azeitao
21	Maranhao	2110807	Sao Felix de Balsas
21	Maranhao	2111607	Sao Raimundo das Mangabeiras
22	Piaui	2201200	Barras
22	Piaui	2201507	Batalha
22	Piaui	2201770	Boa Hora
22	Piaui	2201960	Brasileira
22	Piaui	2202059	Cabeceiras do Piaui
22	Piaui	2202174	Campo Largo do Piaui
22	Piaui	2203701	Esperantina
22	Piaui	2205409	Joaquim Pires
22	Piaui	2205458	Joca Marques
22	Piaui	2205805	Luzilandia
22	Piaui	2205854	Madeiro
22	Piaui	2206100	Matias Olimpio
22	Piaui	2206209	Miguel Alves
22	Piaui	2206670	Morro do Chapeu do Piaui
22	Piaui	2206803	Nossa Senhora dos Remedios
22	Piaui	2208403	Piripiri
22	Piaui	2208502	Porto
22	Piaui	2209971	Sao Joao do Arraial
22	Piaui	2201919	Bom Principio do Piaui
22	Piaui	2202000	Buriti dos Lopes
22	Piaui	2202083	Cajueiro da Praia
22	Piaui	2202539	Caraubas do Piaui
22	Piaui	2202653	Caxingo
22	Piaui	2202703	Cocal
22	Piaui	2202729	Cocal dos Alves
22	Piaui	2204659	Ilha Grande
22	Piaui	2205706	Luis Correia
22	Piaui	2206696	Murici dos Portelas
22	Piaui	2207702	Parnaiba
22	Piaui	2208304	Piracuruca
22	Piaui	2209872	Sao Joao da Fronteira
22	Piaui	2210052	Sao Jose do Divino
22	Piaui	2200400	Altos
22	Piaui	2201606	Beneditinos
22	Piaui	2202737	Coivaras
22	Piaui	2203255	Curralinhos
22	Piaui	2203305	Demerval Lobao
22	Piaui	2205508	Jose de Freitas
22	Piaui	2205557	Lagoa Alegre
22	Piaui	2205581	Lagoa do Piaui
22	Piaui	2206308	Miguel Leao
22	Piaui	2206407	Monsenhor Gil
22	Piaui	2207793	Pau D'Arco do Piaui
22	Piaui	2211001	Teresina
22	Piaui	2211100	Uniao
22	Piaui	2200301	Alto Longa
22	Piaui	2201051	Assuncao do Piaui
22	Piaui	2201945	Boqueirao do Piaui
22	Piaui	2202026	Buriti dos Montes
22	Piaui	2202208	Campo Maior
22	Piaui	2202406	Capitao de Campos
22	Piaui	2202604	Castelo do Piaui
22	Piaui	2202711	Cocal de Telha
22	Piaui	2203420	Domingos Mourao
22	Piaui	2205276	Jatoba do Piaui
22	Piaui	2205516	Juazeiro do Piaui
22	Piaui	2205573	Lagoa de Sao Francisco
22	Piaui	2206357	Milton Brandao
22	Piaui	2206753	Nossa Senhora de Nazare
22	Piaui	2206951	Novo Santo Antonio
22	Piaui	2207900	Pedro II
22	Piaui	2209906	Sao Joao da Serra
22	Piaui	2210409	Sao Miguel do Tapuio
22	Piaui	2210656	Sigefredo Pacheco
22	Piaui	2200103	Agricolandia
22	Piaui	2200202	agua Branca
22	Piaui	2200509	Amarante
22	Piaui	2200608	Angical do Piaui
22	Piaui	2201002	Arraial
22	Piaui	2201408	Barro Duro
22	Piaui	2204105	Francisco Ayres
22	Piaui	2204600	Hugo Napoleao
22	Piaui	2205250	Jardim do Mulato
22	Piaui	2205540	Lagoinha do Piaui
22	Piaui	2207108	Olho D'agua do Piaui
22	Piaui	2207504	Palmeirais
22	Piaui	2207751	Passagem Franca do Piaui
22	Piaui	2208809	Regeneracao
22	Piaui	2209450	Santo Antonio dos Milagres
22	Piaui	2209807	Sao Goncalo do Piaui
22	Piaui	2210508	Sao Pedro do Piaui
22	Piaui	2200905	Aroazes
22	Piaui	2201176	Barra D'Alcantara
22	Piaui	2203503	Elesbao Veloso
22	Piaui	2204006	Francinopolis
22	Piaui	2204709	Inhuma
22	Piaui	2205599	Lagoa do Sitio
22	Piaui	2206902	Novo Oriente do Piaui
22	Piaui	2208106	Pimenteiras
22	Piaui	2208601	Prata do Piaui
22	Piaui	2209153	Santa Cruz dos Milagres
22	Piaui	2209609	Sao Felix do Piaui
22	Piaui	2210383	Sao Miguel da Baixa Grande
22	Piaui	2211308	Valenca do Piaui
22	Piaui	2211407	Varzea Grande
22	Piaui	2201150	Baixa Grande do Ribeiro
22	Piaui	2208908	Ribeiro Goncalves
22	Piaui	2209203	Santa Filomena
22	Piaui	2211209	Urucui
22	Piaui	2200806	Antonio Almeida
22	Piaui	2201705	Bertolinia
22	Piaui	2202752	Colonia do Gurgueia
22	Piaui	2203602	Eliseu Martins
22	Piaui	2205607	Landri Sales
22	Piaui	2205904	Manoel Emidio
22	Piaui	2206001	Marcos Parente
22	Piaui	2208551	Porto Alegre do Piaui
22	Piaui	2210631	Sebastiao Leal
22	Piaui	2202251	Canavieira
22	Piaui	2203800	Flores do Piaui
22	Piaui	2203909	Floriano
22	Piaui	2204501	Guadalupe
22	Piaui	2205102	Itaueira
22	Piaui	2205300	Jerumenha
22	Piaui	2206704	Nazare do Piaui
22	Piaui	2207850	Pavussu
22	Piaui	2209005	Rio Grande do Piaui
22	Piaui	2209708	Sao Francisco do Piaui
22	Piaui	2210102	Sao Jose do Peixe
22	Piaui	2210391	Sao Miguel do Fidalgo
22	Piaui	2200459	Alvorada do Gurgueia
22	Piaui	2201309	Barreiras do Piaui
22	Piaui	2201903	Bom Jesus
22	Piaui	2203107	Cristino Castro
22	Piaui	2203230	Currais
22	Piaui	2204402	Gilbues
22	Piaui	2206605	Monte Alegre do Piaui
22	Piaui	2207405	Palmeira do Piaui
22	Piaui	2208700	Redencao do Gurgueia
22	Piaui	2209302	Santa Luz
22	Piaui	2209757	Sao Goncalo do Gurgueia
22	Piaui	2200707	Anisio de Abreu
22	Piaui	2201929	Bonfim do Piaui
22	Piaui	2201988	Brejo do Piaui
22	Piaui	2202307	Canto do Buriti
22	Piaui	2202505	Caracol
22	Piaui	2202851	Coronel Jose Dias
22	Piaui	2203354	Dirceu Arcoverde
22	Piaui	2203453	Dom Inocencio
22	Piaui	2203750	Fartura do Piaui
22	Piaui	2204550	Guaribas
22	Piaui	2205532	Jurema
22	Piaui	2207355	Pajeu do Piaui
22	Piaui	2209559	Sao Braz do Piaui
22	Piaui	2210359	Sao Lourenco do Piaui
22	Piaui	2210607	Sao Raimundo Nonato
22	Piaui	2210953	Tamboril do Piaui
22	Piaui	2211357	Varzea Branca
22	Piaui	2201101	Avelino Lopes
22	Piaui	2202901	Corrente
22	Piaui	2203008	Cristalandia do Piaui
22	Piaui	2203206	Curimata
22	Piaui	2205524	Julio Borges
22	Piaui	2206654	Morro Cabeca no Tempo
22	Piaui	2207603	Parnagua
22	Piaui	2208858	Riacho Frio
22	Piaui	2210623	Sebastiao Barros
22	Piaui	2200954	Aroeiras do Itaim
22	Piaui	2201804	Bocaina
22	Piaui	2202075	Cajazeiras do Piaui
22	Piaui	2202778	Colonia do Piaui
22	Piaui	2203404	Dom Expedito Lopes
22	Piaui	2204352	Geminiano
22	Piaui	2204808	Ipiranga do Piaui
22	Piaui	2207009	Oeiras
22	Piaui	2207553	Paqueta
22	Piaui	2208007	Picos
22	Piaui	2209104	Santa Cruz do Piaui
22	Piaui	2209351	Santana do Piaui
22	Piaui	2209377	Santa Rosa do Piaui
22	Piaui	2209856	Sao Joao da Canabrava
22	Piaui	2209955	Sao Joao da Varjota
22	Piaui	2210201	Sao Jose do Piaui
22	Piaui	2210375	Sao Luis do Piaui
22	Piaui	2210938	Sussuapara
22	Piaui	2210979	Tanque do Piaui
22	Piaui	2211704	Wall Ferraz
22	Piaui	2200251	Alagoinha do Piaui
22	Piaui	2200277	Alegrete do Piaui
22	Piaui	2204204	Francisco Santos
22	Piaui	2206506	Monsenhor Hipolito
22	Piaui	2208205	Pio IX
22	Piaui	2209401	Santo Antonio de Lisboa
22	Piaui	2210300	Sao Juliao
22	Piaui	2200053	Acaua
22	Piaui	2201556	Bela Vista do Piaui
22	Piaui	2201572	Belem do Piaui
22	Piaui	2201739	Betania do Piaui
22	Piaui	2202091	Caldeirao Grande do Piaui
22	Piaui	2202109	Campinas do Piaui
22	Piaui	2202117	Campo Alegre do Fidalgo
22	Piaui	2202133	Campo Grande do Piaui
22	Piaui	2202455	Capitao Gervasio Oliveira
22	Piaui	2202554	Caridade do Piaui
22	Piaui	2202802	Conceicao do Caninde
22	Piaui	2203271	Curral Novo do Piaui
22	Piaui	2203859	Floresta do Piaui
22	Piaui	2204154	Francisco Macedo
22	Piaui	2204303	Fronteiras
22	Piaui	2204907	Isaias Coelho
22	Piaui	2205003	Itainopolis
22	Piaui	2205151	Jacobina do Piaui
22	Piaui	2205201	Jaicos
22	Piaui	2205359	Joao Costa
22	Piaui	2205565	Lagoa do Barro do Piaui
22	Piaui	2205953	Marcolandia
22	Piaui	2206050	Massape do Piaui
22	Piaui	2207207	Padre Marcos
22	Piaui	2207306	Paes Landim
22	Piaui	2207777	Patos do Piaui
22	Piaui	2207801	Paulistana
22	Piaui	2207934	Pedro Laurentino
22	Piaui	2207959	Nova Santa Rita
22	Piaui	2208650	Queimada Nova
22	Piaui	2208874	Ribeira do Piaui
22	Piaui	2209500	Santo Inacio do Piaui
22	Piaui	2209658	Sao Francisco de Assis do Piaui
22	Piaui	2210003	Sao Joao do Piaui
22	Piaui	2210706	Simoes
22	Piaui	2210805	Simplicio Mendes
22	Piaui	2210904	Socorro do Piaui
22	Piaui	2211506	Vera Mendes
22	Piaui	2211605	Vila Nova do Piaui
23	Ceara	2300200	Acarau
23	Ceara	2302057	Barroquinha
23	Ceara	2302305	Bela Cruz
23	Ceara	2302602	Camocim
23	Ceara	2303907	Chaval
23	Ceara	2304251	Cruz
23	Ceara	2304707	Granja
23	Ceara	2306553	Itarema
23	Ceara	2307254	Jijoca de Jericoacoara
23	Ceara	2307809	Marco
23	Ceara	2307908	Martinopole
23	Ceara	2308906	Morrinhos
23	Ceara	2303402	Carnaubal
23	Ceara	2304236	Croata
23	Ceara	2305001	Guaraciaba do Norte
23	Ceara	2305308	Ibiapina
23	Ceara	2312304	Sao Benedito
23	Ceara	2313401	Tiangua
23	Ceara	2313609	Ubajara
23	Ceara	2314102	Vicosa do Ceara
23	Ceara	2304004	Coreau
23	Ceara	2304509	Frecheirinha
23	Ceara	2308807	Moraujo
23	Ceara	2313906	Uruoca
23	Ceara	2300507	Alcantaras
23	Ceara	2308203	Meruoca
23	Ceara	2303105	Carire
23	Ceara	2304350	Forquilha
23	Ceara	2304657	Graca
23	Ceara	2304905	Groairas
23	Ceara	2306108	Iraucuba
23	Ceara	2308005	Massape
23	Ceara	2308377	Miraima
23	Ceara	2309003	Mucambo
23	Ceara	2309904	Pacuja
23	Ceara	2312007	Santana do Acarau
23	Ceara	2312809	Senador Sa
23	Ceara	2312908	Sobral
23	Ceara	2305803	Ipu
23	Ceara	2305902	Ipueiras
23	Ceara	2310951	Pires Ferreira
23	Ceara	2311009	Poranga
23	Ceara	2311702	Reriutaba
23	Ceara	2313955	Varjota
23	Ceara	2303659	Catunda
23	Ceara	2305209	Hidrolandia
23	Ceara	2312205	Santa Quiteria
23	Ceara	2300754	Amontada
23	Ceara	2306405	Itapipoca
23	Ceara	2313500	Trairi
23	Ceara	2310209	Paracuru
23	Ceara	2310258	Paraipaba
23	Ceara	2312403	Sao Goncalo do Amarante
23	Ceara	2306306	Itapage
23	Ceara	2313559	Tururu
23	Ceara	2313757	Umirim
23	Ceara	2313807	Uruburetama
23	Ceara	2300903	Apuiares
23	Ceara	2304608	General Sampaio
23	Ceara	2310704	Pentecoste
23	Ceara	2312601	Sao Luis do Curu
23	Ceara	2313351	Tejucuoca
23	Ceara	2302800	Caninde
23	Ceara	2303006	Caridade
23	Ceara	2306603	Itatira
23	Ceara	2310407	Paramoti
23	Ceara	2300150	Acarape
23	Ceara	2301208	Aracoiaba
23	Ceara	2301406	Aratuba
23	Ceara	2302107	Baturite
23	Ceara	2302909	Capistrano
23	Ceara	2305100	Guaramiranga
23	Ceara	2306504	Itapiuna
23	Ceara	2309102	Mulungu
23	Ceara	2309805	Pacoti
23	Ceara	2310100	Palmacia
23	Ceara	2311603	Redencao
23	Ceara	2301950	Barreira
23	Ceara	2303956	Chorozinho
23	Ceara	2309458	Ocara
23	Ceara	2302206	Beberibe
23	Ceara	2303501	Cascavel
23	Ceara	2310852	Pindoretama
23	Ceara	2301000	Aquiraz
23	Ceara	2303709	Caucaia
23	Ceara	2304285	Eusebio
23	Ceara	2304400	Fortaleza
23	Ceara	2304954	Guaiuba
23	Ceara	2306256	Itaitinga
23	Ceara	2307650	Maracanau
23	Ceara	2307700	Maranguape
23	Ceara	2309706	Pacatuba
23	Ceara	2305233	Horizonte
23	Ceara	2309607	Pacajus
23	Ceara	2301257	Ararenda
23	Ceara	2304103	Crateus
23	Ceara	2305605	Independencia
23	Ceara	2305654	Ipaporanga
23	Ceara	2308609	Monsenhor Tabosa
23	Ceara	2309300	Nova Russas
23	Ceara	2309409	Novo Oriente
23	Ceara	2311264	Quiterianopolis
23	Ceara	2313203	Tamboril
23	Ceara	2301851	Banabuiu
23	Ceara	2302404	Boa Viagem
23	Ceara	2303931	Choro
23	Ceara	2305266	Ibaretama
23	Ceara	2307635	Madalena
23	Ceara	2311306	Quixada
23	Ceara	2311405	Quixeramobim
23	Ceara	2300408	Aiuaba
23	Ceara	2301505	Arneiroz
23	Ceara	2303600	Catarina
23	Ceara	2310308	Parambu
23	Ceara	2311900	Saboeiro
23	Ceara	2313302	Taua
23	Ceara	2300309	Acopiara
23	Ceara	2304269	Deputado Irapuan Pinheiro
23	Ceara	2308351	Milha
23	Ceara	2308500	Mombaca
23	Ceara	2310506	Pedra Branca
23	Ceara	2310902	Piquet Carneiro
23	Ceara	2312700	Senador Pompeu
23	Ceara	2313005	Solonopole
23	Ceara	2301109	Aracati
23	Ceara	2304459	Fortim
23	Ceara	2305357	Icapui
23	Ceara	2306207	Itaicaba
23	Ceara	2300705	Alto Santo
23	Ceara	2305332	Ibicuitinga
23	Ceara	2307007	Jaguaruana
23	Ceara	2307601	Limoeiro do Norte
23	Ceara	2308708	Morada Nova
23	Ceara	2310001	Palhano
23	Ceara	2311504	Quixere
23	Ceara	2311801	Russas
23	Ceara	2312502	Sao Joao do Jaguaribe
23	Ceara	2313104	Tabuleiro do Norte
23	Ceara	2306702	Jaguaretama
23	Ceara	2306801	Jaguaribara
23	Ceara	2306900	Jaguaribe
23	Ceara	2304277	Erere
23	Ceara	2306009	Iracema
23	Ceara	2310803	Pereiro
23	Ceara	2311231	Potiretama
23	Ceara	2303808	Cedro
23	Ceara	2305407	Ico
23	Ceara	2305506	Iguatu
23	Ceara	2309508	Oros
23	Ceara	2311355	Quixelo
23	Ceara	2300804	Antonina do Norte
23	Ceara	2303303	Carius
23	Ceara	2307403	Jucas
23	Ceara	2313252	Tarrafas
23	Ceara	2314003	Varzea Alegre
23	Ceara	2301802	Baixio
23	Ceara	2305704	Ipaumirim
23	Ceara	2307502	Lavras da Mangabeira
23	Ceara	2313708	Umari
23	Ceara	2301307	Araripe
23	Ceara	2301604	Assare
23	Ceara	2302701	Campos Sales
23	Ceara	2311207	Potengi
23	Ceara	2311959	Salitre
23	Ceara	2300606	Altaneira
23	Ceara	2303204	Caririacu
23	Ceara	2304301	Farias Brito
23	Ceara	2304806	Granjeiro
23	Ceara	2301703	Aurora
23	Ceara	2302008	Barro
23	Ceara	2308104	Mauriti
23	Ceara	2301901	Barbalha
23	Ceara	2304202	Crato
23	Ceara	2307106	Jardim
23	Ceara	2307304	Juazeiro do Norte
23	Ceara	2308401	Missao Velha
23	Ceara	2309201	Nova Olinda
23	Ceara	2311108	Porteiras
23	Ceara	2312106	Santana do Cariri
23	Ceara	2300101	Abaiara
23	Ceara	2302503	Brejo Santo
23	Ceara	2307205	Jati
23	Ceara	2308302	Milagres
23	Ceara	2310605	Penaforte
24	Rio Grande do Norte	2401107	Areia Branca
24	Rio Grande do Norte	2401453	Barauna
24	Rio Grande do Norte	2404408	Grossos
24	Rio Grande do Norte	2408003	Mossoro
24	Rio Grande do Norte	2411056	Tibau
24	Rio Grande do Norte	2413359	Serra do Mel
24	Rio Grande do Norte	2401008	Apodi
24	Rio Grande do Norte	2402303	Caraubas
24	Rio Grande do Norte	2403707	Felipe Guerra
24	Rio Grande do Norte	2404309	Governador Dix-Sept Rosado
24	Rio Grande do Norte	2401305	Augusto Severo
24	Rio Grande do Norte	2405207	Janduis
24	Rio Grande do Norte	2407609	Messias Targino
24	Rio Grande do Norte	2408706	Parau
24	Rio Grande do Norte	2414456	Triunfo Potiguar
24	Rio Grande do Norte	2414605	Upanema
24	Rio Grande do Norte	2400208	Acu
24	Rio Grande do Norte	2400703	Alto do Rodrigues
24	Rio Grande do Norte	2402501	Carnaubais
24	Rio Grande do Norte	2404705	Ipanguacu
24	Rio Grande do Norte	2404853	Itaja
24	Rio Grande do Norte	2406106	Jucurutu
24	Rio Grande do Norte	2409902	Pendencias
24	Rio Grande do Norte	2410256	Porto do Mangue
24	Rio Grande do Norte	2412807	Sao Rafael
24	Rio Grande do Norte	2400406	agua Nova
24	Rio Grande do Norte	2402907	Coronel Joao Pessoa
24	Rio Grande do Norte	2403202	Doutor Severiano
24	Rio Grande do Norte	2403301	Encanto
24	Rio Grande do Norte	2407005	Luis Gomes
24	Rio Grande do Norte	2407252	Major Sales
24	Rio Grande do Norte	2410801	Riacho de Santana
24	Rio Grande do Norte	2412500	Sao Miguel
24	Rio Grande do Norte	2414753	Venha-Ver
24	Rio Grande do Norte	2400505	Alexandria
24	Rio Grande do Norte	2403905	Francisco Dantas
24	Rio Grande do Norte	2404903	Itau
24	Rio Grande do Norte	2406007	Jose da Penha
24	Rio Grande do Norte	2407302	Marcelino Vieira
24	Rio Grande do Norte	2408607	Parana
24	Rio Grande do Norte	2409407	Pau dos Ferros
24	Rio Grande do Norte	2410009	Piloes
24	Rio Grande do Norte	2410207	Portalegre
24	Rio Grande do Norte	2410504	Rafael Fernandes
24	Rio Grande do Norte	2410702	Riacho da Cruz
24	Rio Grande do Norte	2411007	Rodolfo Fernandes
24	Rio Grande do Norte	2411908	Sao Francisco do Oeste
24	Rio Grande do Norte	2413607	Severiano Melo
24	Rio Grande do Norte	2413805	Taboleiro Grande
24	Rio Grande do Norte	2414100	Tenente Ananias
24	Rio Grande do Norte	2414902	Vicosa
24	Rio Grande do Norte	2400604	Almino Afonso
24	Rio Grande do Norte	2400901	Antonio Martins
24	Rio Grande do Norte	2404002	Frutuoso Gomes
24	Rio Grande do Norte	2405900	Joao Dias
24	Rio Grande do Norte	2406908	Lucrecia
24	Rio Grande do Norte	2407401	Martins
24	Rio Grande do Norte	2408409	Olho-d'agua do Borges
24	Rio Grande do Norte	2409308	Patu
24	Rio Grande do Norte	2410603	Rafael Godeiro
24	Rio Grande do Norte	2413557	Serrinha dos Pintos
24	Rio Grande do Norte	2414506	Umarizal
24	Rio Grande do Norte	2401859	Caicara do Norte
24	Rio Grande do Norte	2404101	Galinhos
24	Rio Grande do Norte	2404507	Guamare
24	Rio Grande do Norte	2407203	Macau
24	Rio Grande do Norte	2411601	Sao Bento do Norte
24	Rio Grande do Norte	2400307	Afonso Bezerra
24	Rio Grande do Norte	2400802	Angicos
24	Rio Grande do Norte	2401909	Caicara do Rio do Vento
24	Rio Grande do Norte	2403756	Fernando Pedroza
24	Rio Grande do Norte	2405504	Jardim de Angicos
24	Rio Grande do Norte	2406700	Lajes
24	Rio Grande do Norte	2409605	Pedra Preta
24	Rio Grande do Norte	2409704	Pedro Avelino
24	Rio Grande do Norte	2401651	Bodo
24	Rio Grande do Norte	2402709	Cerro Cora
24	Rio Grande do Norte	2403806	Florania
24	Rio Grande do Norte	2406502	Lagoa Nova
24	Rio Grande do Norte	2411403	Santana do Matos
24	Rio Grande do Norte	2413003	Sao Vicente
24	Rio Grande do Norte	2414159	Tenente Laurentino Cruz
24	Rio Grande do Norte	2402006	Caico
24	Rio Grande do Norte	2404804	Ipueira
24	Rio Grande do Norte	2405603	Jardim de Piranhas
24	Rio Grande do Norte	2411809	Sao Fernando
24	Rio Grande do Norte	2412104	Sao Joao do Sabugi
24	Rio Grande do Norte	2413409	Serra Negra do Norte
24	Rio Grande do Norte	2414308	Timbauba dos Batistas
24	Rio Grande do Norte	2400109	Acari
24	Rio Grande do Norte	2402402	Carnauba dos Dantas
24	Rio Grande do Norte	2403004	Cruzeta
24	Rio Grande do Norte	2403103	Currais Novos
24	Rio Grande do Norte	2403400	Equador
24	Rio Grande do Norte	2405702	Jardim do Serido
24	Rio Grande do Norte	2408508	Ouro Branco
24	Rio Grande do Norte	2408904	Parelhas
24	Rio Grande do Norte	2411429	Santana do Serido
24	Rio Grande do Norte	2412401	Sao Jose do Serido
24	Rio Grande do Norte	2401602	Bento Fernandes
24	Rio Grande do Norte	2405108	Jandaira
24	Rio Grande do Norte	2405801	Joao Camara
24	Rio Grande do Norte	2408805	Parazinho
24	Rio Grande do Norte	2410108	Poco Branco
24	Rio Grande do Norte	2401503	Barcelona
24	Rio Grande do Norte	2402105	Campo Redondo
24	Rio Grande do Norte	2402808	Coronel Ezequiel
24	Rio Grande do Norte	2405009	Jacana
24	Rio Grande do Norte	2405405	Japi
24	Rio Grande do Norte	2406403	Lagoa de Velhos
24	Rio Grande do Norte	2406809	Lajes Pintadas
24	Rio Grande do Norte	2407906	Monte das Gameleiras
24	Rio Grande do Norte	2411106	Ruy Barbosa
24	Rio Grande do Norte	2411205	Santa Cruz
24	Rio Grande do Norte	2411700	Sao Bento do Trairi
24	Rio Grande do Norte	2412302	Sao Jose do Campestre
24	Rio Grande do Norte	2412906	Sao Tome
24	Rio Grande do Norte	2413300	Serra de Sao Bento
24	Rio Grande do Norte	2413706	Sitio Novo
24	Rio Grande do Norte	2414001	Tangara
24	Rio Grande do Norte	2401701	Bom Jesus
24	Rio Grande do Norte	2401800	Brejinho
24	Rio Grande do Norte	2404606	Ielmo Marinho
24	Rio Grande do Norte	2405306	Januario Cicco
24	Rio Grande do Norte	2406155	Jundia
24	Rio Grande do Norte	2406205	Lagoa d'Anta
24	Rio Grande do Norte	2406304	Lagoa de Pedras
24	Rio Grande do Norte	2406601	Lagoa Salgada
24	Rio Grande do Norte	2407807	Monte Alegre
24	Rio Grande do Norte	2408300	Nova Cruz
24	Rio Grande do Norte	2409100	Passa e Fica
24	Rio Grande do Norte	2409209	Passagem
24	Rio Grande do Norte	2409332	Santa Maria
24	Rio Grande do Norte	2410306	Presidente Juscelino
24	Rio Grande do Norte	2410900	Riachuelo
24	Rio Grande do Norte	2411502	Santo Antonio
24	Rio Grande do Norte	2412609	Sao Paulo do Potengi
24	Rio Grande do Norte	2412708	Sao Pedro
24	Rio Grande do Norte	2413102	Senador Eloi de Souza
24	Rio Grande do Norte	2413508	Serrinha
24	Rio Grande do Norte	2414704	Varzea
24	Rio Grande do Norte	2414803	Vera Cruz
24	Rio Grande do Norte	2407500	Maxaranguape
24	Rio Grande do Norte	2408953	Rio do Fogo
24	Rio Grande do Norte	2409506	Pedra Grande
24	Rio Grande do Norte	2410405	Pureza
24	Rio Grande do Norte	2412559	Sao Miguel do Gostoso
24	Rio Grande do Norte	2413904	Taipu
24	Rio Grande do Norte	2414407	Touros
24	Rio Grande do Norte	2402600	Ceara-Mirim
24	Rio Grande do Norte	2407104	Macaiba
24	Rio Grande do Norte	2408201	Nisia Floresta
24	Rio Grande do Norte	2412005	Sao Goncalo do Amarante
24	Rio Grande do Norte	2412203	Sao Jose de Mipibu
24	Rio Grande do Norte	2403251	Parnamirim
24	Rio Grande do Norte	2403608	Extremoz
24	Rio Grande do Norte	2408102	Natal
24	Rio Grande do Norte	2401206	Ares
24	Rio Grande do Norte	2401404	Baia Formosa
24	Rio Grande do Norte	2402204	Canguaretama
24	Rio Grande do Norte	2403509	Espirito Santo
24	Rio Grande do Norte	2404200	Goianinha
24	Rio Grande do Norte	2407708	Montanhas
24	Rio Grande do Norte	2409803	Pedro Velho
24	Rio Grande do Norte	2413201	Senador Georgino Avelino
24	Rio Grande do Norte	2414209	Tibau do Sul
24	Rio Grande do Norte	2415008	Vila Flor
25	Paraiba	2502003	Belem do Brejo do Cruz
25	Paraiba	2502300	Bom Sucesso
25	Paraiba	2502805	Brejo do Cruz
25	Paraiba	2502904	Brejo dos Santos
25	Paraiba	2504306	Catole do Rocha
25	Paraiba	2507408	Jerico
25	Paraiba	2508109	Lagoa
25	Paraiba	2509370	Mato Grosso
25	Paraiba	2512804	Riacho dos Cavalos
25	Paraiba	2513901	Sao Bento
25	Paraiba	2514651	Sao Jose do Brejo do Cruz
25	Paraiba	2500700	Sao Joao do Rio do Peixe
25	Paraiba	2502052	Bernardino Batista
25	Paraiba	2502201	Bom Jesus
25	Paraiba	2502409	Bonito de Santa Fe
25	Paraiba	2503308	Cachoeira dos indios
25	Paraiba	2503704	Cajazeiras
25	Paraiba	2504108	Carrapateira
25	Paraiba	2509602	Monte Horebe
25	Paraiba	2512036	Poco Dantas
25	Paraiba	2512077	Poco de Jose de Moura
25	Paraiba	2513307	Santa Helena
25	Paraiba	2513653	Santarem
25	Paraiba	2514503	Sao Jose de Piranhas
25	Paraiba	2516805	Triunfo
25	Paraiba	2516904	Uirauna
25	Paraiba	2500775	Aparecida
25	Paraiba	2503753	Cajazeirinhas
25	Paraiba	2504504	Condado
25	Paraiba	2505501	Vista Serrana
25	Paraiba	2508406	Lastro
25	Paraiba	2508802	Malta
25	Paraiba	2509156	Marizopolis
25	Paraiba	2510006	Nazarezinho
25	Paraiba	2510907	Paulista
25	Paraiba	2512101	Pombal
25	Paraiba	2513208	Santa Cruz
25	Paraiba	2513927	Sao Bentinho
25	Paraiba	2513968	Sao Domingos de Pombal
25	Paraiba	2513984	Sao Francisco
25	Paraiba	2514206	Sao Jose da Lagoa Tapada
25	Paraiba	2516201	Sousa
25	Paraiba	2517209	Vieiropolis
25	Paraiba	2501153	Areia de Baraunas
25	Paraiba	2503407	Cacimba de Areia
25	Paraiba	2508703	Mae d'agua
25	Paraiba	2510709	Passagem
25	Paraiba	2510808	Patos
25	Paraiba	2512606	Quixaba
25	Paraiba	2513802	Santa Teresinha
25	Paraiba	2514404	Sao Jose de Espinharas
25	Paraiba	2514602	Sao Jose do Bonfim
25	Paraiba	2500205	Aguiar
25	Paraiba	2502607	Igaracy
25	Paraiba	2504207	Catingueira
25	Paraiba	2504801	Coremas
25	Paraiba	2505907	Emas
25	Paraiba	2510204	Nova Olinda
25	Paraiba	2510402	Olho d'agua
25	Paraiba	2511301	Pianco
25	Paraiba	2513604	Santana dos Garrotes
25	Paraiba	2502102	Boa Ventura
25	Paraiba	2504405	Conceicao
25	Paraiba	2505303	Curral Velho
25	Paraiba	2505600	Diamante
25	Paraiba	2506608	Ibiara
25	Paraiba	2507002	Itaporanga
25	Paraiba	2511004	Pedra Branca
25	Paraiba	2513356	Santa Ines
25	Paraiba	2513505	Santana de Mangueira
25	Paraiba	2514305	Sao Jose de Caiana
25	Paraiba	2515708	Serra Grande
25	Paraiba	2500106	agua Branca
25	Paraiba	2503555	Cacimbas
25	Paraiba	2505402	Desterro
25	Paraiba	2506707	Imaculada
25	Paraiba	2508000	Juru
25	Paraiba	2509008	Manaira
25	Paraiba	2509396	Matureia
25	Paraiba	2512309	Princesa Isabel
25	Paraiba	2514552	Sao Jose de Princesa
25	Paraiba	2516607	Tavares
25	Paraiba	2516706	Teixeira
25	Paraiba	2507804	Junco do Serido
25	Paraiba	2513000	Salgadinho
25	Paraiba	2513406	Santa Luzia
25	Paraiba	2514701	Sao Jose do Sabugi
25	Paraiba	2514909	Sao Mamede
25	Paraiba	2517100	Varzea
25	Paraiba	2501534	Barauna
25	Paraiba	2505006	Cubati
25	Paraiba	2506202	Frei Martinho
25	Paraiba	2507705	Juazeirinho
25	Paraiba	2510303	Nova Palmeira
25	Paraiba	2511103	Pedra Lavrada
25	Paraiba	2511400	Picui
25	Paraiba	2515401	Serido
25	Paraiba	2516755	Tenorio
25	Paraiba	2500734	Amparo
25	Paraiba	2501351	Assuncao
25	Paraiba	2503902	Camalau
25	Paraiba	2504702	Congo
25	Paraiba	2504850	Coxixola
25	Paraiba	2508505	Livramento
25	Paraiba	2509701	Monteiro
25	Paraiba	2510600	Ouro Velho
25	Paraiba	2510659	Parari
25	Paraiba	2512200	Prata
25	Paraiba	2514107	Sao Joao do Tigre
25	Paraiba	2514800	Sao Jose dos Cordeiros
25	Paraiba	2515203	Sao Sebastiao do Umbuzeiro
25	Paraiba	2515500	Serra Branca
25	Paraiba	2516300	Sume
25	Paraiba	2516508	Taperoa
25	Paraiba	2517407	Zabele
25	Paraiba	2500536	Alcantil
25	Paraiba	2501575	Barra de Santana
25	Paraiba	2501708	Barra de Sao Miguel
25	Paraiba	2502508	Boqueirao
25	Paraiba	2503100	Cabaceiras
25	Paraiba	2504074	Caraubas
25	Paraiba	2504355	Caturite
25	Paraiba	2506509	Gurjao
25	Paraiba	2512788	Riacho de Santo Antonio
25	Paraiba	2513851	Santo Andre
25	Paraiba	2513943	Sao Domingos do Cariri
25	Paraiba	2514008	Sao Joao do Cariri
25	Paraiba	2500577	Algodao de Jandaira
25	Paraiba	2500908	Arara
25	Paraiba	2501609	Barra de Santa Rosa
25	Paraiba	2505105	Cuite
25	Paraiba	2505352	Damiao
25	Paraiba	2510105	Nova Floresta
25	Paraiba	2510501	Olivedos
25	Paraiba	2512002	Pocinhos
25	Paraiba	2512705	Remigio
25	Paraiba	2516102	Soledade
25	Paraiba	2516151	Sossego
25	Paraiba	2501005	Araruna
25	Paraiba	2503506	Cacimba de Dentro
25	Paraiba	2504157	Casserengue
25	Paraiba	2505709	Dona Ines
25	Paraiba	2512747	Riachao
25	Paraiba	2516003	Solanea
25	Paraiba	2516409	Campo de Santana
25	Paraiba	2501203	Areial
25	Paraiba	2506004	Esperanca
25	Paraiba	2509503	Montadas
25	Paraiba	2515104	Sao Sebastiao de Lagoa de Roca
25	Paraiba	2500304	Alagoa Grande
25	Paraiba	2500403	Alagoa Nova
25	Paraiba	2501104	Areia
25	Paraiba	2501500	Bananeiras
25	Paraiba	2502706	Borborema
25	Paraiba	2509339	Matinhas
25	Paraiba	2511608	Piloes
25	Paraiba	2515906	Serraria
25	Paraiba	2500502	Alagoinha
25	Paraiba	2500809	Aracagi
25	Paraiba	2501906	Belem
25	Paraiba	2503605	Caicara
25	Paraiba	2505204	Cuitegi
25	Paraiba	2505808	Duas Estradas
25	Paraiba	2506301	Guarabira
25	Paraiba	2508208	Lagoa de Dentro
25	Paraiba	2508554	Logradouro
25	Paraiba	2509800	Mulungu
25	Paraiba	2511707	Piloezinhos
25	Paraiba	2511806	Pirpirituba
25	Paraiba	2515609	Serra da Raiz
25	Paraiba	2515930	Sertaozinho
25	Paraiba	2502151	Boa Vista
25	Paraiba	2504009	Campina Grande
25	Paraiba	2506103	Fagundes
25	Paraiba	2508307	Lagoa Seca
25	Paraiba	2509206	Massaranduba
25	Paraiba	2512408	Puxinana
25	Paraiba	2512507	Queimadas
25	Paraiba	2515807	Serra Redonda
25	Paraiba	2503803	Caldas Brandao
25	Paraiba	2506400	Gurinhem
25	Paraiba	2506806	Inga
25	Paraiba	2506905	Itabaiana
25	Paraiba	2507200	Itatuba
25	Paraiba	2507606	Juarez Tavora
25	Paraiba	2509404	Mogeiro
25	Paraiba	2512754	Riachao do Bacamarte
25	Paraiba	2513109	Salgado de Sao Felix
25	Paraiba	2501302	Aroeiras
25	Paraiba	2506251	Gado Bravo
25	Paraiba	2509909	Natuba
25	Paraiba	2513158	Santa Cecilia
25	Paraiba	2517001	Umbuzeiro
25	Paraiba	2501401	Baia da Traicao
25	Paraiba	2504033	Capim
25	Paraiba	2505238	Cuite de Mamanguape
25	Paraiba	2505279	Curral de Cima
25	Paraiba	2507101	Itapororoca
25	Paraiba	2507309	Jacarau
25	Paraiba	2508901	Mamanguape
25	Paraiba	2509057	Marcacao
25	Paraiba	2509305	Mataraca
25	Paraiba	2512721	Pedro Regis
25	Paraiba	2512903	Rio Tinto
25	Paraiba	2504900	Cruz do Espirito Santo
25	Paraiba	2507903	Juripiranga
25	Paraiba	2509107	Mari
25	Paraiba	2511509	Pilar
25	Paraiba	2512762	Riachao do Poco
25	Paraiba	2514453	Sao Jose dos Ramos
25	Paraiba	2515005	Sao Miguel de Taipu
25	Paraiba	2515302	Sape
25	Paraiba	2515971	Sobrado
25	Paraiba	2501807	Bayeux
25	Paraiba	2503209	Cabedelo
25	Paraiba	2504603	Conde
25	Paraiba	2507507	Joao Pessoa
25	Paraiba	2508604	Lucena
25	Paraiba	2513703	Santa Rita
25	Paraiba	2500601	Alhandra
25	Paraiba	2503001	Caapora
25	Paraiba	2511202	Pedras de Fogo
25	Paraiba	2511905	Pitimbu
26	Pernambuco	2601102	Araripina
26	Pernambuco	2602001	Bodoco
26	Pernambuco	2605301	Exu
26	Pernambuco	2606309	Granito
26	Pernambuco	2607307	Ipubi
26	Pernambuco	2609907	Ouricuri
26	Pernambuco	2612455	Santa Cruz
26	Pernambuco	2612554	Santa Filomena
26	Pernambuco	2614303	Moreilandia
26	Pernambuco	2615607	Trindade
26	Pernambuco	2604304	Cedro
26	Pernambuco	2609303	Mirandiba
26	Pernambuco	2610400	Parnamirim
26	Pernambuco	2612208	Salgueiro
26	Pernambuco	2613503	Sao Jose do Belmonte
26	Pernambuco	2614006	Serrita
26	Pernambuco	2616100	Verdejante
26	Pernambuco	2600104	Afogados da Ingazeira
26	Pernambuco	2602506	Brejinho
26	Pernambuco	2603405	Calumbi
26	Pernambuco	2603900	Carnaiba
26	Pernambuco	2605608	Flores
26	Pernambuco	2606903	Iguaraci
26	Pernambuco	2607109	Ingazeira
26	Pernambuco	2607703	Itapetim
26	Pernambuco	2611533	Quixaba
26	Pernambuco	2612471	Santa Cruz da Baixa Verde
26	Pernambuco	2612802	Santa Terezinha
26	Pernambuco	2613602	Sao Jose do Egito
26	Pernambuco	2613909	Serra Talhada
26	Pernambuco	2614402	Solidao
26	Pernambuco	2614600	Tabira
26	Pernambuco	2615706	Triunfo
26	Pernambuco	2615904	Tuparetama
26	Pernambuco	2601201	Arcoverde
26	Pernambuco	2601805	Betania
26	Pernambuco	2605103	Custodia
26	Pernambuco	2606606	Ibimirim
26	Pernambuco	2607000	Inaja
26	Pernambuco	2609154	Manari
26	Pernambuco	2614105	Sertania
26	Pernambuco	2600203	Afranio
26	Pernambuco	2603009	Cabrobo
26	Pernambuco	2605152	Dormentes
26	Pernambuco	2608750	Lagoa Grande
26	Pernambuco	2609808	Oroco
26	Pernambuco	2611101	Petrolina
26	Pernambuco	2612604	Santa Maria da Boa Vista
26	Pernambuco	2615201	Terra Nova
26	Pernambuco	2601607	Belem de Sao Francisco
26	Pernambuco	2603926	Carnaubeira da Penha
26	Pernambuco	2605707	Floresta
26	Pernambuco	2607406	Itacuruba
26	Pernambuco	2608057	Jatoba
26	Pernambuco	2611002	Petrolandia
26	Pernambuco	2614808	Tacaratu
26	Pernambuco	2600500	aguas Belas
26	Pernambuco	2602803	Buique
26	Pernambuco	2607505	Itaiba
26	Pernambuco	2610806	Pedra
26	Pernambuco	2615805	Tupanatinga
26	Pernambuco	2616001	Venturosa
26	Pernambuco	2600609	Alagoinha
26	Pernambuco	2601706	Belo Jardim
26	Pernambuco	2601904	Bezerros
26	Pernambuco	2602605	Brejo da Madre de Deus
26	Pernambuco	2603108	Cachoeirinha
26	Pernambuco	2603801	Capoeiras
26	Pernambuco	2604106	Caruaru
26	Pernambuco	2606408	Gravata
26	Pernambuco	2608008	Jatauba
26	Pernambuco	2610905	Pesqueira
26	Pernambuco	2611200	Pocao
26	Pernambuco	2611705	Riacho das Almas
26	Pernambuco	2612406	Sanharo
26	Pernambuco	2613008	Sao Bento do Una
26	Pernambuco	2613107	Sao Caitano
26	Pernambuco	2614709	Tacaimbo
26	Pernambuco	2604155	Casinhas
26	Pernambuco	2605806	Frei Miguelinho
26	Pernambuco	2612505	Santa Cruz do Capibaribe
26	Pernambuco	2612703	Santa Maria do Cambuca
26	Pernambuco	2614501	Surubim
26	Pernambuco	2615003	Taquaritinga do Norte
26	Pernambuco	2615409	Toritama
26	Pernambuco	2616183	Vertente do Lerio
26	Pernambuco	2616209	Vertentes
26	Pernambuco	2602209	Bom Jardim
26	Pernambuco	2604908	Cumaru
26	Pernambuco	2605400	Feira Nova
26	Pernambuco	2608107	Joao Alfredo
26	Pernambuco	2608909	Limoeiro
26	Pernambuco	2609105	Machados
26	Pernambuco	2609709	Orobo
26	Pernambuco	2610509	Passira
26	Pernambuco	2612109	Salgadinho
26	Pernambuco	2613800	Sao Vicente Ferrer
26	Pernambuco	2601003	Angelim
26	Pernambuco	2602100	Bom Conselho
26	Pernambuco	2602407	Brejao
26	Pernambuco	2603207	Caetes
26	Pernambuco	2603306	Calcado
26	Pernambuco	2603702	Canhotinho
26	Pernambuco	2604700	Correntes
26	Pernambuco	2606002	Garanhuns
26	Pernambuco	2606507	Iati
26	Pernambuco	2608255	Jucati
26	Pernambuco	2608305	Jupi
26	Pernambuco	2608404	Jurema
26	Pernambuco	2608602	Lagoa do Ouro
26	Pernambuco	2608800	Lajedo
26	Pernambuco	2610103	Palmeirina
26	Pernambuco	2610301	Paranatama
26	Pernambuco	2612307	Saloa
26	Pernambuco	2613206	Sao Joao
26	Pernambuco	2615102	Terezinha
26	Pernambuco	2600302	Agrestina
26	Pernambuco	2600807	Altinho
26	Pernambuco	2601300	Barra de Guabiraba
26	Pernambuco	2602308	Bonito
26	Pernambuco	2603504	Camocim de Sao Felix
26	Pernambuco	2605004	Cupira
26	Pernambuco	2606705	Ibirajuba
26	Pernambuco	2608701	Lagoa dos Gatos
26	Pernambuco	2610202	Panelas
26	Pernambuco	2612000	Saire
26	Pernambuco	2613305	Sao Joaquim do Monte
26	Pernambuco	2600708	Alianca
26	Pernambuco	2602704	Buenos Aires
26	Pernambuco	2603603	Camutanga
26	Pernambuco	2604007	Carpina
26	Pernambuco	2604601	Condado
26	Pernambuco	2605509	Ferreiros
26	Pernambuco	2606200	Goiana
26	Pernambuco	2607653	Itambe
26	Pernambuco	2607802	Itaquitinga
26	Pernambuco	2608453	Lagoa do Carro
26	Pernambuco	2608503	Lagoa do Itaenga
26	Pernambuco	2609006	Macaparana
26	Pernambuco	2609501	Nazare da Mata
26	Pernambuco	2610608	Paudalho
26	Pernambuco	2615300	Timbauba
26	Pernambuco	2615508	Tracunhaem
26	Pernambuco	2616308	Vicencia
26	Pernambuco	2604403	Cha de Alegria
26	Pernambuco	2604502	Cha Grande
26	Pernambuco	2606101	Gloria do Goita
26	Pernambuco	2611309	Pombos
26	Pernambuco	2616407	Vitoria de Santo Antao
26	Pernambuco	2600401	agua Preta
26	Pernambuco	2600906	Amaraji
26	Pernambuco	2601409	Barreiros
26	Pernambuco	2601508	Belem de Maria
26	Pernambuco	2604205	Catende
26	Pernambuco	2604809	Cortes
26	Pernambuco	2605202	Escada
26	Pernambuco	2605905	Gameleira
26	Pernambuco	2607950	Jaqueira
26	Pernambuco	2608206	Joaquim Nabuco
26	Pernambuco	2609204	Maraial
26	Pernambuco	2610004	Palmares
26	Pernambuco	2611408	Primavera
26	Pernambuco	2611507	Quipapa
26	Pernambuco	2611804	Ribeirao
26	Pernambuco	2611903	Rio Formoso
26	Pernambuco	2612901	Sao Benedito do Sul
26	Pernambuco	2613404	Sao Jose da Coroa Grande
26	Pernambuco	2614204	Sirinhaem
26	Pernambuco	2614857	Tamandare
26	Pernambuco	2616506	Xexeu
26	Pernambuco	2601052	Aracoiaba
26	Pernambuco	2606804	Igarassu
26	Pernambuco	2607604	Ilha de Itamaraca
26	Pernambuco	2607752	Itapissuma
26	Pernambuco	2600054	Abreu e Lima
26	Pernambuco	2603454	Camaragibe
26	Pernambuco	2607901	Jaboatao dos Guararapes
26	Pernambuco	2609402	Moreno
26	Pernambuco	2609600	Olinda
26	Pernambuco	2610707	Paulista
26	Pernambuco	2611606	Recife
26	Pernambuco	2613701	Sao Lourenco da Mata
26	Pernambuco	2602902	Cabo de Santo Agostinho
26	Pernambuco	2607208	Ipojuca
26	Pernambuco	2605459	Fernando de Noronha
27	Alagoas	2700102	agua Branca
27	Alagoas	2701605	Canapi
27	Alagoas	2703304	Inhapi
27	Alagoas	2705002	Mata Grande
27	Alagoas	2706422	Pariconha
27	Alagoas	2702405	Delmiro Gouveia
27	Alagoas	2705804	Olho d'agua do Casado
27	Alagoas	2707107	Piranhas
27	Alagoas	2701803	Carneiros
27	Alagoas	2702504	Dois Riachos
27	Alagoas	2704609	Maravilha
27	Alagoas	2706109	Ouro Branco
27	Alagoas	2706208	Palestina
27	Alagoas	2706406	Pao de Acucar
27	Alagoas	2707206	Poco das Trincheiras
27	Alagoas	2708006	Santana do Ipanema
27	Alagoas	2708402	Sao Jose da Tapera
27	Alagoas	2708956	Senador Rui Palmeira
27	Alagoas	2700706	Batalha
27	Alagoas	2700904	Belo Monte
27	Alagoas	2703403	Jacare dos Homens
27	Alagoas	2703700	Jaramataia
27	Alagoas	2704401	Major Isidoro
27	Alagoas	2705408	Monteiropolis
27	Alagoas	2705705	Olho d'agua das Flores
27	Alagoas	2706000	Olivenca
27	Alagoas	2700805	Belem
27	Alagoas	2701209	Cacimbinhas
27	Alagoas	2702553	Estrela de Alagoas
27	Alagoas	2703106	Igaci
27	Alagoas	2704807	Maribondo
27	Alagoas	2704906	Mar Vermelho
27	Alagoas	2705309	Minador do Negrao
27	Alagoas	2706307	Palmeira dos indios
27	Alagoas	2706604	Paulo Jacinto
27	Alagoas	2707602	Quebrangulo
27	Alagoas	2709004	Tanque d'Arca
27	Alagoas	2700300	Arapiraca
27	Alagoas	2701506	Campo Grande
27	Alagoas	2702009	Coite do Noia
27	Alagoas	2702355	Craibas
27	Alagoas	2702603	Feira Grande
27	Alagoas	2702900	Girau do Ponciano
27	Alagoas	2704104	Lagoa da Canoa
27	Alagoas	2704203	Limoeiro de Anadia
27	Alagoas	2708808	Sao Sebastiao
27	Alagoas	2709103	Taquarana
27	Alagoas	2705903	Olho d'agua Grande
27	Alagoas	2708204	Sao Bras
27	Alagoas	2709202	Traipu
27	Alagoas	2701902	Cha Preta
27	Alagoas	2703007	Ibateguara
27	Alagoas	2707008	Pindoba
27	Alagoas	2708105	Santana do Mundau
27	Alagoas	2708303	Sao Jose da Laje
27	Alagoas	2709301	Uniao dos Palmares
27	Alagoas	2709400	Vicosa
27	Alagoas	2700409	Atalaia
27	Alagoas	2701100	Branquinha
27	Alagoas	2701308	Cajueiro
27	Alagoas	2701357	Campestre
27	Alagoas	2701704	Capela
27	Alagoas	2702108	Colonia Leopoldina
27	Alagoas	2702801	Flexeiras
27	Alagoas	2703502	Jacuipe
27	Alagoas	2703809	Joaquim Gomes
27	Alagoas	2703908	Jundia
27	Alagoas	2705101	Matriz de Camaragibe
27	Alagoas	2705200	Messias
27	Alagoas	2705507	Murici
27	Alagoas	2705606	Novo Lino
27	Alagoas	2707305	Porto Calvo
27	Alagoas	2708501	Sao Luis do Quitunde
27	Alagoas	2703601	Japaratinga
27	Alagoas	2704500	Maragogi
27	Alagoas	2706505	Passo de Camaragibe
27	Alagoas	2707404	Porto de Pedras
27	Alagoas	2708709	Sao Miguel dos Milagres
27	Alagoas	2700508	Barra de Santo Antonio
27	Alagoas	2700607	Barra de Sao Miguel
27	Alagoas	2702207	Coqueiro Seco
27	Alagoas	2704302	Maceio
27	Alagoas	2704708	Marechal Deodoro
27	Alagoas	2706448	Paripueira
27	Alagoas	2706901	Pilar
27	Alagoas	2707701	Rio Largo
27	Alagoas	2707909	Santa Luzia do Norte
27	Alagoas	2708907	Satuba
27	Alagoas	2700201	Anadia
27	Alagoas	2701001	Boca da Mata
27	Alagoas	2701407	Campo Alegre
27	Alagoas	2702306	Coruripe
27	Alagoas	2703759	Jequia da Praia
27	Alagoas	2704005	Junqueiro
27	Alagoas	2707800	Roteiro
27	Alagoas	2708600	Sao Miguel dos Campos
27	Alagoas	2709152	Teotonio Vilela
27	Alagoas	2702702	Feliz Deserto
27	Alagoas	2703205	Igreja Nova
27	Alagoas	2706703	Penedo
27	Alagoas	2706802	Piacabucu
27	Alagoas	2707503	Porto Real do Colegio
28	Sergipe	2801207	Caninde de Sao Francisco
28	Sergipe	2802205	Feira Nova
28	Sergipe	2802403	Gararu
28	Sergipe	2802601	Gracho Cardoso
28	Sergipe	2803104	Itabi
28	Sergipe	2804201	Monte Alegre de Sergipe
28	Sergipe	2804508	Nossa Senhora da Gloria
28	Sergipe	2805406	Poco Redondo
28	Sergipe	2805604	Porto da Folha
28	Sergipe	2801405	Carira
28	Sergipe	2802304	Frei Paulo
28	Sergipe	2804458	Nossa Senhora Aparecida
28	Sergipe	2805000	Pedra Mole
28	Sergipe	2805208	Pinhao
28	Sergipe	2806008	Ribeiropolis
28	Sergipe	2800209	Aquidaba
28	Sergipe	2801900	Cumbe
28	Sergipe	2803807	Malhada dos Bois
28	Sergipe	2804300	Muribeca
28	Sergipe	2804607	Nossa Senhora das Dores
28	Sergipe	2807006	Sao Miguel do Aleixo
28	Sergipe	2800506	Areia Branca
28	Sergipe	2801009	Campo do Brito
28	Sergipe	2802908	Itabaiana
28	Sergipe	2803708	Macambira
28	Sergipe	2803906	Malhador
28	Sergipe	2804102	Moita Bonita
28	Sergipe	2806800	Sao Domingos
28	Sergipe	2805505	Poco Verde
28	Sergipe	2807105	Simao Dias
28	Sergipe	2807402	Tobias Barreto
28	Sergipe	2803500	Lagarto
28	Sergipe	2805802	Riachao do Dantas
28	Sergipe	2800100	Amparo de Sao Francisco
28	Sergipe	2800704	Brejo Grande
28	Sergipe	2801108	Canhoba
28	Sergipe	2801603	Cedro de Sao Joao
28	Sergipe	2802700	Ilha das Flores
28	Sergipe	2804409	Neopolis
28	Sergipe	2804706	Nossa Senhora de Lourdes
28	Sergipe	2805703	Propria
28	Sergipe	2806404	Santana do Sao Francisco
28	Sergipe	2807303	Telha
28	Sergipe	2801306	Capela
28	Sergipe	2802007	Divina Pastora
28	Sergipe	2806503	Santa Rosa de Lima
28	Sergipe	2807204	Siriri
28	Sergipe	2803302	Japaratuba
28	Sergipe	2803401	Japoata
28	Sergipe	2804904	Pacatuba
28	Sergipe	2805307	Pirambu
28	Sergipe	2806909	Sao Francisco
28	Sergipe	2801504	Carmopolis
28	Sergipe	2802502	General Maynard
28	Sergipe	2803609	Laranjeiras
28	Sergipe	2804003	Maruim
28	Sergipe	2805901	Riachuelo
28	Sergipe	2806107	Rosario do Catete
28	Sergipe	2806602	Santo Amaro das Brotas
28	Sergipe	2800308	Aracaju
28	Sergipe	2800605	Barra dos Coqueiros
28	Sergipe	2804805	Nossa Senhora do Socorro
28	Sergipe	2806701	Sao Cristovao
28	Sergipe	2800407	Araua
28	Sergipe	2800670	Boquim
28	Sergipe	2801702	Cristinapolis
28	Sergipe	2803005	Itabaianinha
28	Sergipe	2805109	Pedrinhas
28	Sergipe	2806206	Salgado
28	Sergipe	2807501	Tomar do Geru
28	Sergipe	2807600	Umbauba
28	Sergipe	2802106	Estancia
28	Sergipe	2802809	Indiaroba
28	Sergipe	2803203	Itaporanga d'Ajuda
28	Sergipe	2806305	Santa Luzia do Itanhy
29	Bahia	2902500	Baianopolis
29	Bahia	2903201	Barreiras
29	Bahia	2907400	Catolandia
29	Bahia	2911105	Formosa do Rio Preto
29	Bahia	2919553	Luis Eduardo Magalhaes
29	Bahia	2926202	Riachao das Neves
29	Bahia	2928901	Sao Desiderio
29	Bahia	2901403	Angical
29	Bahia	2904407	Brejolandia
29	Bahia	2909406	Cotegipe
29	Bahia	2909703	Cristopolis
29	Bahia	2920452	Mansidao
29	Bahia	2928406	Santa Rita de Cassia
29	Bahia	2930907	Tabocas do Brejo Velho
29	Bahia	2933455	Wanderley
29	Bahia	2906105	Canapolis
29	Bahia	2908101	Cocos
29	Bahia	2909109	Coribe
29	Bahia	2909307	Correntina
29	Bahia	2917359	Jaborandi
29	Bahia	2928109	Santa Maria da Vitoria
29	Bahia	2928208	Santana
29	Bahia	2929057	Sao Felix do Coribe
29	Bahia	2930303	Serra Dourada
29	Bahia	2905909	Campo Alegre de Lourdes
29	Bahia	2907202	Casa Nova
29	Bahia	2909901	Curaca
29	Bahia	2918407	Juazeiro
29	Bahia	2924405	Pilao Arcado
29	Bahia	2926004	Remanso
29	Bahia	2930204	Sento Se
29	Bahia	2930774	Sobradinho
29	Bahia	2900207	Abare
29	Bahia	2907707	Chorrocho
29	Bahia	2911402	Gloria
29	Bahia	2919900	Macurure
29	Bahia	2924009	Paulo Afonso
29	Bahia	2927101	Rodelas
29	Bahia	2902708	Barra
29	Bahia	2904753	Buritirama
29	Bahia	2913200	Ibotirama
29	Bahia	2915353	Itaguacu da Bahia
29	Bahia	2921609	Morpara
29	Bahia	2922250	Muquem de Sao Francisco
29	Bahia	2933604	Xique-Xique
29	Bahia	2903904	Bom Jesus da Lapa
29	Bahia	2907103	Carinhanha
29	Bahia	2910776	Feira da Mata
29	Bahia	2923704	Paratinga
29	Bahia	2930154	Serra do Ramalho
29	Bahia	2930758	Sitio do Mato
29	Bahia	2901353	Andorinha
29	Bahia	2901809	Antonio Goncalves
29	Bahia	2906006	Campo Formoso
29	Bahia	2910859	Filadelfia
29	Bahia	2917003	Itiuba
29	Bahia	2917706	Jaguarari
29	Bahia	2924603	Pindobacu
29	Bahia	2930105	Senhor do Bonfim
29	Bahia	2932457	Umburanas
29	Bahia	2901155	America Dourada
29	Bahia	2903003	Barra do Mendes
29	Bahia	2903235	Barro Alto
29	Bahia	2905305	Cafarnaum
29	Bahia	2906204	Canarana
29	Bahia	2907608	Central
29	Bahia	2911303	Gentio do Ouro
29	Bahia	2912400	Ibipeba
29	Bahia	2913101	Ibitita
29	Bahia	2914406	Iraquara
29	Bahia	2914604	Irece
29	Bahia	2918357	Joao Dourado
29	Bahia	2918506	Jussara
29	Bahia	2919157	Lapao
29	Bahia	2922052	Mulungu do Morro
29	Bahia	2925600	Presidente Dutra
29	Bahia	2929255	Sao Gabriel
29	Bahia	2930808	Souto Soares
29	Bahia	2932408	Uibai
29	Bahia	2905107	Caem
29	Bahia	2905503	Caldeirao Grande
29	Bahia	2906873	Capim Grosso
29	Bahia	2917508	Jacobina
29	Bahia	2921203	Miguel Calmon
29	Bahia	2921401	Mirangaba
29	Bahia	2921708	Morro do Chapeu
29	Bahia	2923357	Ourolandia
29	Bahia	2924801	Piritiba
29	Bahia	2925253	Ponto Novo
29	Bahia	2925931	Quixabeira
29	Bahia	2929370	Sao Jose do Jacuipe
29	Bahia	2929800	Saude
29	Bahia	2930600	Serrolandia
29	Bahia	2933109	Varzea do Poco
29	Bahia	2933158	Varzea Nova
29	Bahia	2902609	Baixa Grande
29	Bahia	2903805	Boa Vista do Tupim
29	Bahia	2911907	Iacu
29	Bahia	2912608	Ibiquera
29	Bahia	2914703	Itaberaba
29	Bahia	2919009	Lajedinho
29	Bahia	2919603	Macajuba
29	Bahia	2920106	Mairi
29	Bahia	2922102	Mundo Novo
29	Bahia	2927200	Ruy Barbosa
29	Bahia	2931301	Tapiramuta
29	Bahia	2933059	Varzea da Roca
29	Bahia	2900405	agua Fria
29	Bahia	2901502	Anguera
29	Bahia	2901700	Antonio Cardoso
29	Bahia	2908200	Conceicao da Feira
29	Bahia	2908507	Conceicao do Jacuipe
29	Bahia	2908903	Coracao de Maria
29	Bahia	2910305	Elisio Medrado
29	Bahia	2910800	Feira de Santana
29	Bahia	2913804	Ipecaeta
29	Bahia	2914000	Ipira
29	Bahia	2914505	Irara
29	Bahia	2916856	Itatim
29	Bahia	2923308	Ouricangas
29	Bahia	2924108	Pedrao
29	Bahia	2924652	Pintadas
29	Bahia	2925956	Rafael Jambeiro
29	Bahia	2927507	Santa Barbara
29	Bahia	2928307	Santanopolis
29	Bahia	2928505	Santa Teresinha
29	Bahia	2928802	Santo Estevao
29	Bahia	2929305	Sao Goncalo dos Campos
29	Bahia	2930402	Serra Preta
29	Bahia	2931103	Tanquinho
29	Bahia	2931400	Teodoro Sampaio
29	Bahia	2909208	Coronel Joao Sa
29	Bahia	2918100	Jeremoabo
29	Bahia	2924207	Pedro Alexandre
29	Bahia	2927606	Santa Brigida
29	Bahia	2930766	Sitio do Quinto
29	Bahia	2906808	Cansancao
29	Bahia	2906824	Canudos
29	Bahia	2910701	Euclides da Cunha
29	Bahia	2921500	Monte Santo
29	Bahia	2922656	Nordestina
29	Bahia	2925808	Queimadas
29	Bahia	2925907	Quijingue
29	Bahia	2931905	Tucano
29	Bahia	2932002	Uaua
29	Bahia	2900355	Adustina
29	Bahia	2901601	Antas
29	Bahia	2902658	Banzae
29	Bahia	2907806	Cicero Dantas
29	Bahia	2907905	Cipo
29	Bahia	2910750	Fatima
29	Bahia	2911857	Heliopolis
29	Bahia	2916500	Itapicuru
29	Bahia	2922904	Nova Soure
29	Bahia	2923050	Novo Triunfo
29	Bahia	2923100	Olindina
29	Bahia	2923803	Paripiranga
29	Bahia	2926509	Ribeira do Amparo
29	Bahia	2926608	Ribeira do Pombal
29	Bahia	2902104	Araci
29	Bahia	2903276	Barrocas
29	Bahia	2903607	Biritinga
29	Bahia	2906402	Candeal
29	Bahia	2906857	Capela do Alto Alegre
29	Bahia	2908408	Conceicao do Coite
29	Bahia	2911253	Gaviao
29	Bahia	2913309	Ichu
29	Bahia	2919108	Lamarao
29	Bahia	2922730	Nova Fatima
29	Bahia	2924058	Pe de Serra
29	Bahia	2926103	Retirolandia
29	Bahia	2926301	Riachao do Jacuipe
29	Bahia	2928000	Santaluz
29	Bahia	2928950	Sao Domingos
29	Bahia	2930501	Serrinha
29	Bahia	2931509	Teofilandia
29	Bahia	2933000	Valente
29	Bahia	2900306	Acajutiba
29	Bahia	2900702	Alagoinhas
29	Bahia	2901908	Apora
29	Bahia	2902054	Aracas
29	Bahia	2902203	Aramari
29	Bahia	2909604	Crisopolis
29	Bahia	2913705	Inhambupe
29	Bahia	2927002	Rio Real
29	Bahia	2929701	Satiro Dias
29	Bahia	2907004	Cardeal da Silva
29	Bahia	2908606	Conde
29	Bahia	2910503	Entre Rios
29	Bahia	2910602	Esplanada
29	Bahia	2917904	Jandaira
29	Bahia	2901106	Amelia Rodrigues
29	Bahia	2907509	Catu
29	Bahia	2915908	Itanagra
29	Bahia	2921005	Mata de Sao Joao
29	Bahia	2925204	Pojuca
29	Bahia	2929503	Sao Sebastiao do Passe
29	Bahia	2931707	Terra Nova
29	Bahia	2902302	Aratuipe
29	Bahia	2904852	Cabaceiras do Paraguacu
29	Bahia	2904902	Cachoeira
29	Bahia	2907301	Castro Alves
29	Bahia	2908309	Conceicao do Almeida
29	Bahia	2909802	Cruz das Almas
29	Bahia	2910206	Dom Macedo Costa
29	Bahia	2911600	Governador Mangabeira
29	Bahia	2917805	Jaguaripe
29	Bahia	2920601	Maragogipe
29	Bahia	2922201	Muniz Ferreira
29	Bahia	2922300	Muritiba
29	Bahia	2922508	Nazare
29	Bahia	2927309	Salinas da Margarida
29	Bahia	2928604	Santo Amaro
29	Bahia	2928703	Santo Antonio de Jesus
29	Bahia	2929008	Sao Felix
29	Bahia	2929107	Sao Felipe
29	Bahia	2929602	Sapeacu
29	Bahia	2929750	Saubara
29	Bahia	2933174	Varzedo
29	Bahia	2905701	Camacari
29	Bahia	2906501	Candeias
29	Bahia	2910057	Dias d'avila
29	Bahia	2916104	Itaparica
29	Bahia	2919207	Lauro de Freitas
29	Bahia	2919926	Madre de Deus
29	Bahia	2927408	Salvador
29	Bahia	2929206	Sao Francisco do Conde
29	Bahia	2930709	Simoes Filho
29	Bahia	2933208	Vera Cruz
29	Bahia	2904100	Boquira
29	Bahia	2904209	Botupora
29	Bahia	2904506	Brotas de Macaubas
29	Bahia	2907558	Caturama
29	Bahia	2912509	Ibipitanga
29	Bahia	2913002	Ibitiara
29	Bahia	2914109	Ipupiara
29	Bahia	2919801	Macaubas
29	Bahia	2923035	Novo Horizonte
29	Bahia	2923209	Oliveira dos Brejinhos
29	Bahia	2931053	Tanque Novo
29	Bahia	2900108	Abaira
29	Bahia	2901304	Andarai
29	Bahia	2902807	Barra da Estiva
29	Bahia	2904001	Boninal
29	Bahia	2904050	Bonito
29	Bahia	2908804	Contendas do Sincora
29	Bahia	2912202	Ibicoara
29	Bahia	2915007	Itaete
29	Bahia	2918605	Jussiape
29	Bahia	2919306	Lencois
29	Bahia	2921906	Mucuge
29	Bahia	2922854	Nova Redencao
29	Bahia	2923506	Palmeiras
29	Bahia	2924306	Piata
29	Bahia	2926707	Rio de Contas
29	Bahia	2929909	Seabra
29	Bahia	2932804	Utinga
29	Bahia	2933406	Wagner
29	Bahia	2900603	Aiquara
29	Bahia	2901007	Amargosa
29	Bahia	2901957	Apuarema
29	Bahia	2904308	Brejoes
29	Bahia	2909505	Cravolandia
29	Bahia	2914208	Irajuba
29	Bahia	2914307	Iramaia
29	Bahia	2915106	Itagi
29	Bahia	2916708	Itaquara
29	Bahia	2916906	Itirucu
29	Bahia	2917607	Jaguaquara
29	Bahia	2918001	Jequie
29	Bahia	2918209	Jiquirica
29	Bahia	2918308	Jitauna
29	Bahia	2918704	Lafaiete Coutinho
29	Bahia	2918803	Laje
29	Bahia	2919058	Lajedo do Tabocal
29	Bahia	2920502	Maracas
29	Bahia	2920809	Marcionilio Souza
29	Bahia	2921302	Milagres
29	Bahia	2922409	Mutuipe
29	Bahia	2922805	Nova Itarana
29	Bahia	2924900	Planaltino
29	Bahia	2927903	Santa Ines
29	Bahia	2929404	Sao Miguel das Matas
29	Bahia	2932101	Ubaira
29	Bahia	2900504	erico Cardoso
29	Bahia	2910107	Dom Basilio
29	Bahia	2919504	Livramento de Nossa Senhora
29	Bahia	2923605	Paramirim
29	Bahia	2926905	Rio do Pires
29	Bahia	2905008	Cacule
29	Bahia	2905206	Caetite
29	Bahia	2906600	Candiba
29	Bahia	2911709	Guanambi
29	Bahia	2912004	Ibiassuce
29	Bahia	2913408	Igapora
29	Bahia	2917334	Iuiu
29	Bahia	2917409	Jacaraci
29	Bahia	2918753	Lagoa Real
29	Bahia	2919405	Licinio de Almeida
29	Bahia	2920205	Malhada
29	Bahia	2921054	Matina
29	Bahia	2921807	Mortugaba
29	Bahia	2923407	Palmas de Monte Alto
29	Bahia	2924504	Pindai
29	Bahia	2926400	Riacho de Santana
29	Bahia	2930006	Sebastiao Laranjeiras
29	Bahia	2932606	Urandi
29	Bahia	2902005	Aracatu
29	Bahia	2904605	Brumado
29	Bahia	2906899	Caraibas
29	Bahia	2908705	Condeuba
29	Bahia	2909000	Cordeiros
29	Bahia	2911659	Guajeru
29	Bahia	2917201	Ituacu
29	Bahia	2919959	Maetinga
29	Bahia	2920304	Malhada de Pedras
29	Bahia	2924702	Piripa
29	Bahia	2925709	Presidente Janio Quadros
29	Bahia	2926806	Rio do Antonio
29	Bahia	2931004	Tanhacu
29	Bahia	2931806	Tremedal
29	Bahia	2901205	Anage
29	Bahia	2902906	Barra do Choca
29	Bahia	2903508	Belo Campo
29	Bahia	2903706	Boa Nova
29	Bahia	2903953	Bom Jesus da Serra
29	Bahia	2904803	Caatiba
29	Bahia	2905156	Caetanos
29	Bahia	2906709	Candido Sales
29	Bahia	2910008	Dario Meira
29	Bahia	2912301	Ibicui
29	Bahia	2913507	Iguai
29	Bahia	2920403	Manoel Vitorino
29	Bahia	2921450	Mirante
29	Bahia	2922706	Nova Canaa
29	Bahia	2925006	Planalto
29	Bahia	2925105	Pocoes
29	Bahia	2933307	Vitoria da Conquista
29	Bahia	2910404	Encruzilhada
29	Bahia	2915809	Itambe
29	Bahia	2916401	Itapetinga
29	Bahia	2916807	Itarantim
29	Bahia	2917102	Itororo
29	Bahia	2919702	Macarani
29	Bahia	2920007	Maiquinique
29	Bahia	2925402	Potiragua
29	Bahia	2926657	Ribeirao do Largo
29	Bahia	2905404	Cairu
29	Bahia	2905800	Camamu
29	Bahia	2913457	Igrapiuna
29	Bahia	2917300	Itubera
29	Bahia	2920700	Marau
29	Bahia	2922607	Nilo Pecanha
29	Bahia	2924678	Pirai do Norte
29	Bahia	2925758	Presidente Tancredo Neves
29	Bahia	2931202	Taperoa
29	Bahia	2932903	Valenca
29	Bahia	2900900	Almadina
29	Bahia	2902252	Arataca
29	Bahia	2902401	Aurelino Leal
29	Bahia	2903102	Barra do Rocha
29	Bahia	2903300	Barro Preto
29	Bahia	2903409	Belmonte
29	Bahia	2904704	Buerarema
29	Bahia	2905602	Camacan
29	Bahia	2906303	Canavieiras
29	Bahia	2908002	Coaraci
29	Bahia	2910909	Firmino Alves
29	Bahia	2911006	Floresta Azul
29	Bahia	2911204	Gandu
29	Bahia	2911501	Gongogi
29	Bahia	2912103	Ibicarai
29	Bahia	2912707	Ibirapitanga
29	Bahia	2912905	Ibirataia
29	Bahia	2913606	Ilheus
29	Bahia	2913903	Ipiau
29	Bahia	2914802	Itabuna
29	Bahia	2914901	Itacare
29	Bahia	2915205	Itagiba
29	Bahia	2915403	Itaju do Colonia
29	Bahia	2915502	Itajuipe
29	Bahia	2915700	Itamari
29	Bahia	2916203	Itape
29	Bahia	2916302	Itapebi
29	Bahia	2916609	Itapitanga
29	Bahia	2918555	Jussari
29	Bahia	2920908	Mascote
29	Bahia	2922755	Nova Ibia
29	Bahia	2923902	Pau Brasil
29	Bahia	2927804	Santa Cruz da Vitoria
29	Bahia	2928059	Santa Luzia
29	Bahia	2929354	Sao Jose da Vitoria
29	Bahia	2931608	Teolandia
29	Bahia	2932200	Ubaitaba
29	Bahia	2932309	Ubata
29	Bahia	2932507	Una
29	Bahia	2932705	Urucuca
29	Bahia	2933505	Wenceslau Guimaraes
29	Bahia	2900801	Alcobaca
29	Bahia	2906907	Caravelas
29	Bahia	2910727	Eunapolis
29	Bahia	2911808	Guaratinga
29	Bahia	2912806	Ibirapua
29	Bahia	2914653	Itabela
29	Bahia	2915304	Itagimirim
29	Bahia	2915601	Itamaraju
29	Bahia	2916005	Itanhem
29	Bahia	2918456	Jucurucu
29	Bahia	2918902	Lajedao
29	Bahia	2921104	Medeiros Neto
29	Bahia	2922003	Mucuri
29	Bahia	2923001	Nova Vicosa
29	Bahia	2925303	Porto Seguro
29	Bahia	2925501	Prado
29	Bahia	2927705	Santa Cruz Cabralia
29	Bahia	2931350	Teixeira de Freitas
29	Bahia	2933257	Vereda
31	Minas Gerais	3104502	Arinos
31	Minas Gerais	3108206	Bonfinopolis de Minas
31	Minas Gerais	3109303	Buritis
31	Minas Gerais	3109451	Cabeceira Grande
31	Minas Gerais	3122470	Dom Bosco
31	Minas Gerais	3126208	Formoso
31	Minas Gerais	3144375	Natalandia
31	Minas Gerais	3170404	Unai
31	Minas Gerais	3170479	Uruana de Minas
31	Minas Gerais	3108552	Brasilandia de Minas
31	Minas Gerais	3128600	Guarda-Mor
31	Minas Gerais	3136306	Joao Pinheiro
31	Minas Gerais	3137106	Lagamar
31	Minas Gerais	3137536	Lagoa Grande
31	Minas Gerais	3147006	Paracatu
31	Minas Gerais	3153400	Presidente Olegario
31	Minas Gerais	3161700	Sao Goncalo do Abaete
31	Minas Gerais	3170750	Varjao de Minas
31	Minas Gerais	3171006	Vazante
31	Minas Gerais	3108255	Bonito de Minas
31	Minas Gerais	3116159	Chapada Gaucha
31	Minas Gerais	3117836	Conego Marinho
31	Minas Gerais	3130051	Icarai de Minas
31	Minas Gerais	3132107	Itacarambi
31	Minas Gerais	3135209	Januaria
31	Minas Gerais	3136959	Juvenilia
31	Minas Gerais	3139300	Manga
31	Minas Gerais	3140852	Matias Cardoso
31	Minas Gerais	3142254	Miravania
31	Minas Gerais	3142700	Montalvania
31	Minas Gerais	3149150	Pedras de Maria da Cruz
31	Minas Gerais	3150570	Pintopolis
31	Minas Gerais	3161106	Sao Francisco
31	Minas Gerais	3162450	Sao Joao das Missoes
31	Minas Gerais	3170529	Urucuia
31	Minas Gerais	3115474	Catuti
31	Minas Gerais	3124302	Espinosa
31	Minas Gerais	3127339	Gameleiras
31	Minas Gerais	3135050	Jaiba
31	Minas Gerais	3135100	Janauba
31	Minas Gerais	3139250	Mamonas
31	Minas Gerais	3141009	Mato Verde
31	Minas Gerais	3142908	Monte Azul
31	Minas Gerais	3145059	Nova Porteirinha
31	Minas Gerais	3146552	Pai Pedro
31	Minas Gerais	3152204	Porteirinha
31	Minas Gerais	3154507	Riacho dos Machados
31	Minas Gerais	3166956	Serranopolis de Minas
31	Minas Gerais	3101003	aguas Vermelhas
31	Minas Gerais	3106655	Berizal
31	Minas Gerais	3120870	Curral de Dentro
31	Minas Gerais	3122355	Divisa Alegre
31	Minas Gerais	3127073	Fruta de Leite
31	Minas Gerais	3130655	Indaiabira
31	Minas Gerais	3143450	Montezuma
31	Minas Gerais	3144656	Ninheira
31	Minas Gerais	3145372	Novorizonte
31	Minas Gerais	3155603	Rio Pardo de Minas
31	Minas Gerais	3156502	Rubelita
31	Minas Gerais	3157005	Salinas
31	Minas Gerais	3157377	Santa Cruz de Salinas
31	Minas Gerais	3160454	Santo Antonio do Retiro
31	Minas Gerais	3162708	Sao Joao do Paraiso
31	Minas Gerais	3168002	Taiobeiras
31	Minas Gerais	3170651	Vargem Grande do Rio Pardo
31	Minas Gerais	3109402	Buritizeiro
31	Minas Gerais	3129608	Ibiai
31	Minas Gerais	3135605	Jequitai
31	Minas Gerais	3137304	Lagoa dos Patos
31	Minas Gerais	3138104	Lassance
31	Minas Gerais	3151206	Pirapora
31	Minas Gerais	3154457	Riachinho
31	Minas Gerais	3157609	Santa Fe de Minas
31	Minas Gerais	3164209	Sao Romao
31	Minas Gerais	3170800	Varzea da Palma
31	Minas Gerais	3108602	Brasilia de Minas
31	Minas Gerais	3111150	Campo Azul
31	Minas Gerais	3112703	Capitao Eneas
31	Minas Gerais	3116506	Claro dos Pocoes
31	Minas Gerais	3118809	Coracao de Jesus
31	Minas Gerais	3126703	Francisco Sa
31	Minas Gerais	3127354	Glaucilandia
31	Minas Gerais	3129657	Ibiracatu
31	Minas Gerais	3135357	Japonvar
31	Minas Gerais	3136801	Juramento
31	Minas Gerais	3138658	Lontra
31	Minas Gerais	3138682	Luislandia
31	Minas Gerais	3142007	Mirabela
31	Minas Gerais	3143302	Montes Claros
31	Minas Gerais	3147956	Patis
31	Minas Gerais	3152131	Ponto Chique
31	Minas Gerais	3162252	Sao Joao da Lagoa
31	Minas Gerais	3162401	Sao Joao da Ponte
31	Minas Gerais	3162658	Sao Joao do Pacui
31	Minas Gerais	3170008	Ubai
31	Minas Gerais	3170909	Varzelandia
31	Minas Gerais	3171030	Verdelandia
31	Minas Gerais	3108503	Botumirim
31	Minas Gerais	3120300	Cristalia
31	Minas Gerais	3127800	Grao Mogol
31	Minas Gerais	3132008	Itacambira
31	Minas Gerais	3136579	Josenopolis
31	Minas Gerais	3146255	Padre Carvalho
31	Minas Gerais	3107307	Bocaiuva
31	Minas Gerais	3123809	Engenheiro Navarro
31	Minas Gerais	3126604	Francisco Dumont
31	Minas Gerais	3128253	Guaraciama
31	Minas Gerais	3145455	Olhos-d'agua
31	Minas Gerais	3120102	Couto de Magalhaes de Minas
31	Minas Gerais	3121001	Datas
31	Minas Gerais	3121605	Diamantina
31	Minas Gerais	3125408	Felicio dos Santos
31	Minas Gerais	3125507	Sao Goncalo do Rio Preto
31	Minas Gerais	3127602	Gouveia
31	Minas Gerais	3153301	Presidente Kubitschek
31	Minas Gerais	3165909	Senador Modestino Goncalves
31	Minas Gerais	3102852	Angelandia
31	Minas Gerais	3104452	Aricanduva
31	Minas Gerais	3106507	Berilo
31	Minas Gerais	3112307	Capelinha
31	Minas Gerais	3113503	Carbonita
31	Minas Gerais	3116100	Chapada do Norte
31	Minas Gerais	3126505	Francisco Badaro
31	Minas Gerais	3132503	Itamarandiba
31	Minas Gerais	3135456	Jenipapo de Minas
31	Minas Gerais	3136520	Jose Goncalves de Minas
31	Minas Gerais	3138351	Leme do Prado
31	Minas Gerais	3141801	Minas Novas
31	Minas Gerais	3169703	Turmalina
31	Minas Gerais	3171071	Veredinha
31	Minas Gerais	3103405	Aracuai
31	Minas Gerais	3113008	Carai
31	Minas Gerais	3119500	Coronel Murta
31	Minas Gerais	3134004	Itinga
31	Minas Gerais	3145307	Novo Cruzeiro
31	Minas Gerais	3146305	Padre Paraiso
31	Minas Gerais	3152170	Ponto dos Volantes
31	Minas Gerais	3171600	Virgem da Lapa
31	Minas Gerais	3102704	Cachoeira de Pajeu
31	Minas Gerais	3117009	Comercinho
31	Minas Gerais	3133303	Itaobim
31	Minas Gerais	3141405	Medina
31	Minas Gerais	3148707	Pedra Azul
31	Minas Gerais	3101706	Almenara
31	Minas Gerais	3105202	Bandeira
31	Minas Gerais	3122454	Divisopolis
31	Minas Gerais	3125606	Felisburgo
31	Minas Gerais	3134707	Jacinto
31	Minas Gerais	3135803	Jequitinhonha
31	Minas Gerais	3136009	Joaima
31	Minas Gerais	3136504	Jordania
31	Minas Gerais	3140555	Mata Verde
31	Minas Gerais	3143153	Monte Formoso
31	Minas Gerais	3146750	Palmopolis
31	Minas Gerais	3155108	Rio do Prado
31	Minas Gerais	3156601	Rubim
31	Minas Gerais	3157104	Salto da Divisa
31	Minas Gerais	3158102	Santa Maria do Salto
31	Minas Gerais	3160306	Santo Antonio do Jacinto
31	Minas Gerais	3104700	Ataleia
31	Minas Gerais	3115458	Catuji
31	Minas Gerais	3126752	Franciscopolis
31	Minas Gerais	3126802	Frei Gaspar
31	Minas Gerais	3132305	Itaipe
31	Minas Gerais	3137007	Ladainha
31	Minas Gerais	3139201	Malacacheta
31	Minas Gerais	3145356	Novo Oriente de Minas
31	Minas Gerais	3146206	Ouro Verde de Minas
31	Minas Gerais	3148509	Pavao
31	Minas Gerais	3152402	Pote
31	Minas Gerais	3165552	Setubinha
31	Minas Gerais	3168606	Teofilo Otoni
31	Minas Gerais	3100906	aguas Formosas
31	Minas Gerais	3106606	Bertopolis
31	Minas Gerais	3113701	Carlos Chagas
31	Minas Gerais	3120151	Crisolita
31	Minas Gerais	3127057	Fronteira dos Vales
31	Minas Gerais	3138906	Machacalis
31	Minas Gerais	3144300	Nanuque
31	Minas Gerais	3157658	Santa Helena de Minas
31	Minas Gerais	3166709	Serra dos Aimores
31	Minas Gerais	3170305	Umburatiba
31	Minas Gerais	3109808	Cachoeira Dourada
31	Minas Gerais	3112604	Capinopolis
31	Minas Gerais	3129103	Gurinhata
31	Minas Gerais	3131406	Ipiacu
31	Minas Gerais	3134202	Ituiutaba
31	Minas Gerais	3159803	Santa Vitoria
31	Minas Gerais	3103504	Araguari
31	Minas Gerais	3103751	Arapora
31	Minas Gerais	3111804	Canapolis
31	Minas Gerais	3115003	Cascalho Rico
31	Minas Gerais	3115805	Centralina
31	Minas Gerais	3130705	Indianopolis
31	Minas Gerais	3142809	Monte Alegre de Minas
31	Minas Gerais	3152808	Prata
31	Minas Gerais	3169604	Tupaciguara
31	Minas Gerais	3170206	Uberlandia
31	Minas Gerais	3100104	Abadia dos Dourados
31	Minas Gerais	3119302	Coromandel
31	Minas Gerais	3120706	Cruzeiro da Fortaleza
31	Minas Gerais	3123502	Douradoquara
31	Minas Gerais	3124807	Estrela do Sul
31	Minas Gerais	3127909	Grupiara
31	Minas Gerais	3131604	Irai de Minas
31	Minas Gerais	3143104	Monte Carmelo
31	Minas Gerais	3148103	Patrocinio
31	Minas Gerais	3156403	Romaria
31	Minas Gerais	3166808	Serra do Salitre
31	Minas Gerais	3103801	Arapua
31	Minas Gerais	3114303	Carmo do Paranaiba
31	Minas Gerais	3128907	Guimarania
31	Minas Gerais	3137502	Lagoa Formosa
31	Minas Gerais	3141207	Matutina
31	Minas Gerais	3148004	Patos de Minas
31	Minas Gerais	3155504	Rio Paranaiba
31	Minas Gerais	3159704	Santa Rosa da Serra
31	Minas Gerais	3162104	Sao Gotardo
31	Minas Gerais	3168903	Tiros
31	Minas Gerais	3111101	Campina Verde
31	Minas Gerais	3114550	Carneirinho
31	Minas Gerais	3116902	Comendador Gomes
31	Minas Gerais	3127008	Fronteira
31	Minas Gerais	3127107	Frutal
31	Minas Gerais	3133402	Itapagipe
31	Minas Gerais	3134400	Iturama
31	Minas Gerais	3138625	Limeira do Oeste
31	Minas Gerais	3150703	Pirajuba
31	Minas Gerais	3151602	Planura
31	Minas Gerais	3161304	Sao Francisco de Sales
31	Minas Gerais	3170438	Uniao de Minas
31	Minas Gerais	3100708	agua Comprida
31	Minas Gerais	3111408	Campo Florido
31	Minas Gerais	3117306	Conceicao das Alagoas
31	Minas Gerais	3118205	Conquista
31	Minas Gerais	3121258	Delta
31	Minas Gerais	3170107	Uberaba
31	Minas Gerais	3171105	Verissimo
31	Minas Gerais	3104007	Araxa
31	Minas Gerais	3111507	Campos Altos
31	Minas Gerais	3129509	Ibia
31	Minas Gerais	3145000	Nova Ponte
31	Minas Gerais	3149200	Pedrinopolis
31	Minas Gerais	3149804	Perdizes
31	Minas Gerais	3153004	Pratinha
31	Minas Gerais	3156908	Sacramento
31	Minas Gerais	3157708	Santa Juliana
31	Minas Gerais	3168101	Tapira
31	Minas Gerais	3100203	Abaete
31	Minas Gerais	3107000	Biquinhas
31	Minas Gerais	3115607	Cedro do Abaete
31	Minas Gerais	3143500	Morada Nova de Minas
31	Minas Gerais	3146404	Paineiras
31	Minas Gerais	3152006	Pompeu
31	Minas Gerais	3169356	Tres Marias
31	Minas Gerais	3104809	Augusto de Lima
31	Minas Gerais	3109204	Buenopolis
31	Minas Gerais	3119104	Corinto
31	Minas Gerais	3120904	Curvelo
31	Minas Gerais	3125705	Felixlandia
31	Minas Gerais	3131109	Inimutaba
31	Minas Gerais	3136405	Joaquim Felicio
31	Minas Gerais	3142502	Monjolos
31	Minas Gerais	3143609	Morro da Garca
31	Minas Gerais	3153202	Presidente Juscelino
31	Minas Gerais	3160603	Santo Hipolito
31	Minas Gerais	3103900	Araujos
31	Minas Gerais	3107406	Bom Despacho
31	Minas Gerais	3123205	Dores do Indaia
31	Minas Gerais	3124708	Estrela do Indaia
31	Minas Gerais	3135308	Japaraiba
31	Minas Gerais	3137205	Lagoa da Prata
31	Minas Gerais	3138302	Leandro Ferreira
31	Minas Gerais	3138807	Luz
31	Minas Gerais	3140506	Martinho Campos
31	Minas Gerais	3142403	Moema
31	Minas Gerais	3153707	Quartel Geral
31	Minas Gerais	3166600	Serra da Saudade
31	Minas Gerais	3103207	Aracai
31	Minas Gerais	3105004	Baldim
31	Minas Gerais	3109600	Cachoeira da Prata
31	Minas Gerais	3109907	Caetanopolis
31	Minas Gerais	3112505	Capim Branco
31	Minas Gerais	3118908	Cordisburgo
31	Minas Gerais	3126406	Fortuna de Minas
31	Minas Gerais	3127206	Funilandia
31	Minas Gerais	3131000	Inhauma
31	Minas Gerais	3134608	Jaboticatubas
31	Minas Gerais	3135704	Jequitiba
31	Minas Gerais	3139706	Maravilhas
31	Minas Gerais	3141108	Matozinhos
31	Minas Gerais	3146909	Papagaios
31	Minas Gerais	3147402	Paraopeba
31	Minas Gerais	3149606	Pequi
31	Minas Gerais	3153608	Prudente de Morais
31	Minas Gerais	3158508	Santana de Pirapama
31	Minas Gerais	3159001	Santana do Riacho
31	Minas Gerais	3167202	Sete Lagoas
31	Minas Gerais	3102407	Alvorada de Minas
31	Minas Gerais	3117504	Conceicao do Mato Dentro
31	Minas Gerais	3118106	Congonhas do Norte
31	Minas Gerais	3122603	Dom Joaquim
31	Minas Gerais	3132800	Itambe do Mato Dentro
31	Minas Gerais	3143708	Morro do Pilar
31	Minas Gerais	3147501	Passabem
31	Minas Gerais	3156007	Rio Vermelho
31	Minas Gerais	3160207	Santo Antonio do Itambe
31	Minas Gerais	3160504	Santo Antonio do Rio Abaixo
31	Minas Gerais	3164803	Sao Sebastiao do Rio Preto
31	Minas Gerais	3166501	Serra Azul de Minas
31	Minas Gerais	3167103	Serro
31	Minas Gerais	3126000	Florestal
31	Minas Gerais	3145802	Onca de Pitangui
31	Minas Gerais	3147105	Para de Minas
31	Minas Gerais	3151404	Pitangui
31	Minas Gerais	3163102	Sao Jose da Varginha
31	Minas Gerais	3106200	Belo Horizonte
31	Minas Gerais	3106705	Betim
31	Minas Gerais	3109006	Brumadinho
31	Minas Gerais	3110004	Caete
31	Minas Gerais	3117876	Confins
31	Minas Gerais	3118601	Contagem
31	Minas Gerais	3124104	Esmeraldas
31	Minas Gerais	3129806	Ibirite
31	Minas Gerais	3130101	Igarape
31	Minas Gerais	3136652	Juatuba
31	Minas Gerais	3137601	Lagoa Santa
31	Minas Gerais	3140159	Mario Campos
31	Minas Gerais	3140704	Mateus Leme
31	Minas Gerais	3144805	Nova Lima
31	Minas Gerais	3149309	Pedro Leopoldo
31	Minas Gerais	3153905	Raposos
31	Minas Gerais	3154606	Ribeirao das Neves
31	Minas Gerais	3154804	Rio Acima
31	Minas Gerais	3156700	Sabara
31	Minas Gerais	3157807	Santa Luzia
31	Minas Gerais	3162922	Sao Joaquim de Bicas
31	Minas Gerais	3162955	Sao Jose da Lapa
31	Minas Gerais	3165537	Sarzedo
31	Minas Gerais	3171204	Vespasiano
31	Minas Gerais	3102308	Alvinopolis
31	Minas Gerais	3105400	Barao de Cocais
31	Minas Gerais	3106002	Bela Vista de Minas
31	Minas Gerais	3107703	Bom Jesus do Amparo
31	Minas Gerais	3115359	Catas Altas
31	Minas Gerais	3121803	Dionisio
31	Minas Gerais	3125903	Ferros
31	Minas Gerais	3131703	Itabira
31	Minas Gerais	3136207	Joao Monlevade
31	Minas Gerais	3136603	Nova Uniao
31	Minas Gerais	3144706	Nova Era
31	Minas Gerais	3155702	Rio Piracicaba
31	Minas Gerais	3157203	Santa Barbara
31	Minas Gerais	3158003	Santa Maria de Itabira
31	Minas Gerais	3161007	Sao Domingos do Prata
31	Minas Gerais	3161908	Sao Goncalo do Rio Abaixo
31	Minas Gerais	3163409	Sao Jose do Goiabal
31	Minas Gerais	3168309	Taquaracu de Minas
31	Minas Gerais	3106408	Belo Vale
31	Minas Gerais	3108107	Bonfim
31	Minas Gerais	3120607	Crucilandia
31	Minas Gerais	3132206	Itaguara
31	Minas Gerais	3133709	Itatiaiucu
31	Minas Gerais	3135407	Jeceaba
31	Minas Gerais	3142304	Moeda
31	Minas Gerais	3150406	Piedade dos Gerais
31	Minas Gerais	3155306	Rio Manso
31	Minas Gerais	3121704	Diogo de Vasconcelos
31	Minas Gerais	3131901	Itabirito
31	Minas Gerais	3140001	Mariana
31	Minas Gerais	3146107	Ouro Preto
31	Minas Gerais	3114907	Casa Grande
31	Minas Gerais	3115409	Catas Altas da Noruega
31	Minas Gerais	3118007	Congonhas
31	Minas Gerais	3118304	Conselheiro Lafaiete
31	Minas Gerais	3120409	Cristiano Otoni
31	Minas Gerais	3121407	Desterro de Entre Rios
31	Minas Gerais	3123908	Entre Rios de Minas
31	Minas Gerais	3133907	Itaverava
31	Minas Gerais	3145901	Ouro Branco
31	Minas Gerais	3153806	Queluzito
31	Minas Gerais	3159100	Santana dos Montes
31	Minas Gerais	3160900	Sao Bras do Suacui
31	Minas Gerais	3108800	Braunas
31	Minas Gerais	3113800	Carmesia
31	Minas Gerais	3116803	Coluna
31	Minas Gerais	3122207	Divinolandia de Minas
31	Minas Gerais	3123106	Dores de Guanhaes
31	Minas Gerais	3127503	Gonzaga
31	Minas Gerais	3128006	Guanhaes
31	Minas Gerais	3140605	Materlandia
31	Minas Gerais	3148400	Paulistas
31	Minas Gerais	3156809	Sabinopolis
31	Minas Gerais	3157500	Santa Efigenia de Minas
31	Minas Gerais	3162807	Sao Joao Evangelista
31	Minas Gerais	3165503	Sardoa
31	Minas Gerais	3166105	Senhora do Porto
31	Minas Gerais	3171808	Virginopolis
31	Minas Gerais	3100609	agua Boa
31	Minas Gerais	3112059	Cantagalo
31	Minas Gerais	3126950	Frei Lagonegro
31	Minas Gerais	3136553	Jose Raydan
31	Minas Gerais	3148608	Pecanha
31	Minas Gerais	3158201	Santa Maria do Suacui
31	Minas Gerais	3163508	Sao Jose do Jacuri
31	Minas Gerais	3164100	Sao Pedro do Suacui
31	Minas Gerais	3164506	Sao Sebastiao do Maranhao
31	Minas Gerais	3101805	Alpercata
31	Minas Gerais	3110806	Campanario
31	Minas Gerais	3112653	Capitao Andrade
31	Minas Gerais	3119203	Coroaci
31	Minas Gerais	3122108	Divino das Laranjeiras
31	Minas Gerais	3123700	Engenheiro Caldas
31	Minas Gerais	3125804	Fernandes Tourinho
31	Minas Gerais	3126901	Frei Inocencio
31	Minas Gerais	3127305	Galileia
31	Minas Gerais	3127701	Governador Valadares
31	Minas Gerais	3132701	Itambacuri
31	Minas Gerais	3133204	Itanhomi
31	Minas Gerais	3135076	Jampruca
31	Minas Gerais	3140100	Marilac
31	Minas Gerais	3144201	Nacip Raydan
31	Minas Gerais	3144904	Nova Modica
31	Minas Gerais	3150000	Pescador
31	Minas Gerais	3161601	Sao Geraldo da Piedade
31	Minas Gerais	3161650	Sao Geraldo do Baixio
31	Minas Gerais	3163003	Sao Jose da Safira
31	Minas Gerais	3163300	Sao Jose do Divino
31	Minas Gerais	3167707	Sobralia
31	Minas Gerais	3169505	Tumiritinga
31	Minas Gerais	3171501	Mathias Lobato
31	Minas Gerais	3171907	Virgolandia
31	Minas Gerais	3115706	Central de Minas
31	Minas Gerais	3131802	Itabirinha
31	Minas Gerais	3139607	Mantena
31	Minas Gerais	3141504	Mendes Pimentel
31	Minas Gerais	3144672	Nova Belem
31	Minas Gerais	3161056	Sao Felix de Minas
31	Minas Gerais	3162575	Sao Joao do Manteninha
31	Minas Gerais	3100500	Acucena
31	Minas Gerais	3103009	Antonio Dias
31	Minas Gerais	3106309	Belo Oriente
31	Minas Gerais	3119401	Coronel Fabriciano
31	Minas Gerais	3131307	Ipatinga
31	Minas Gerais	3135001	Jaguaracu
31	Minas Gerais	3136108	Joanesia
31	Minas Gerais	3140308	Marlieria
31	Minas Gerais	3141702	Mesquita
31	Minas Gerais	3144359	Naque
31	Minas Gerais	3149952	Periquito
31	Minas Gerais	3158953	Santana do Paraiso
31	Minas Gerais	3168705	Timoteo
31	Minas Gerais	3107802	Bom Jesus do Galho
31	Minas Gerais	3109253	Bugre
31	Minas Gerais	3113404	Caratinga
31	Minas Gerais	3120003	Corrego Novo
31	Minas Gerais	3122504	Dom Cavati
31	Minas Gerais	3123858	Entre Folhas
31	Minas Gerais	3129301	Iapu
31	Minas Gerais	3130556	Imbe de Minas
31	Minas Gerais	3130903	Inhapim
31	Minas Gerais	3131158	Ipaba
31	Minas Gerais	3150158	Piedade de Caratinga
31	Minas Gerais	3150539	Pingo-d'agua
31	Minas Gerais	3157252	Santa Barbara do Leste
31	Minas Gerais	3159357	Santa Rita de Minas
31	Minas Gerais	3160959	Sao Domingos das Dores
31	Minas Gerais	3162609	Sao Joao do Oriente
31	Minas Gerais	3164472	Sao Sebastiao do Anta
31	Minas Gerais	3168408	Tarumirim
31	Minas Gerais	3170057	Ubaporanga
31	Minas Gerais	3170578	Vargem Alegre
31	Minas Gerais	3101102	Aimores
31	Minas Gerais	3102209	Alvarenga
31	Minas Gerais	3117405	Conceicao de Ipanema
31	Minas Gerais	3118403	Conselheiro Pena
31	Minas Gerais	3120839	Cuparaque
31	Minas Gerais	3127370	Goiabeira
31	Minas Gerais	3131208	Ipanema
31	Minas Gerais	3134103	Itueta
31	Minas Gerais	3144003	Mutum
31	Minas Gerais	3151909	Pocrane
31	Minas Gerais	3154309	Resplendor
31	Minas Gerais	3159506	Santa Rita do Itueto
31	Minas Gerais	3168051	Taparuba
31	Minas Gerais	3105103	Bambui
31	Minas Gerais	3119807	Corrego Danta
31	Minas Gerais	3123403	Doresopolis
31	Minas Gerais	3130309	Iguatama
31	Minas Gerais	3141306	Medeiros
31	Minas Gerais	3151503	Piumhi
31	Minas Gerais	3164308	Sao Roque de Minas
31	Minas Gerais	3168200	Tapirai
31	Minas Gerais	3170602	Vargem Bonita
31	Minas Gerais	3114204	Carmo do Cajuru
31	Minas Gerais	3116605	Claudio
31	Minas Gerais	3117603	Conceicao do Para
31	Minas Gerais	3122306	Divinopolis
31	Minas Gerais	3130200	Igaratinga
31	Minas Gerais	3133808	Itauna
31	Minas Gerais	3145208	Nova Serrana
31	Minas Gerais	3149705	Perdigao
31	Minas Gerais	3160405	Santo Antonio do Monte
31	Minas Gerais	3161809	Sao Goncalo do Para
31	Minas Gerais	3164605	Sao Sebastiao do Oeste
31	Minas Gerais	3104205	Arcos
31	Minas Gerais	3110400	Camacho
31	Minas Gerais	3119955	Corrego Fundo
31	Minas Gerais	3126109	Formiga
31	Minas Gerais	3133501	Itapecerica
31	Minas Gerais	3146503	Pains
31	Minas Gerais	3148905	Pedra do Indaia
31	Minas Gerais	3150505	Pimenta
31	Minas Gerais	3100807	Aguanil
31	Minas Gerais	3111200	Campo Belo
31	Minas Gerais	3111903	Cana Verde
31	Minas Gerais	3112000	Candeias
31	Minas Gerais	3120201	Cristais
31	Minas Gerais	3149903	Perdoes
31	Minas Gerais	3158805	Santana do Jacare
31	Minas Gerais	3108008	Bom Sucesso
31	Minas Gerais	3114006	Carmo da Mata
31	Minas Gerais	3114501	Carmopolis de Minas
31	Minas Gerais	3130002	Ibituruna
31	Minas Gerais	3145604	Oliveira
31	Minas Gerais	3147709	Passa Tempo
31	Minas Gerais	3150604	Piracema
31	Minas Gerais	3159902	Santo Antonio do Amparo
31	Minas Gerais	3161205	Sao Francisco de Paula
31	Minas Gerais	3101904	Alpinopolis
31	Minas Gerais	3107604	Bom Jesus da Penha
31	Minas Gerais	3112406	Capetinga
31	Minas Gerais	3112802	Capitolio
31	Minas Gerais	3115102	Cassia
31	Minas Gerais	3116407	Claraval
31	Minas Gerais	3121209	Delfinopolis
31	Minas Gerais	3126307	Fortaleza de Minas
31	Minas Gerais	3129707	Ibiraci
31	Minas Gerais	3133758	Itau de Minas
31	Minas Gerais	3147907	Passos
31	Minas Gerais	3152907	Pratapolis
31	Minas Gerais	3162203	Sao Joao Batista do Gloria
31	Minas Gerais	3162948	Sao Jose da Barra
31	Minas Gerais	3104106	Arceburgo
31	Minas Gerais	3109501	Cabo Verde
31	Minas Gerais	3128303	Guaranesia
31	Minas Gerais	3128709	Guaxupe
31	Minas Gerais	3132909	Itamogi
31	Minas Gerais	3134806	Jacui
31	Minas Gerais	3136900	Juruaia
31	Minas Gerais	3143005	Monte Belo
31	Minas Gerais	3143203	Monte Santo de Minas
31	Minas Gerais	3144102	Muzambinho
31	Minas Gerais	3145109	Nova Resende
31	Minas Gerais	3163904	Sao Pedro da Uniao
31	Minas Gerais	3164704	Sao Sebastiao do Paraiso
31	Minas Gerais	3165107	Sao Tomas de Aquino
31	Minas Gerais	3101607	Alfenas
31	Minas Gerais	3102001	Alterosa
31	Minas Gerais	3104304	Areado
31	Minas Gerais	3114402	Carmo do Rio Claro
31	Minas Gerais	3114709	Carvalhopolis
31	Minas Gerais	3117108	Conceicao da Aparecida
31	Minas Gerais	3122405	Divisa Nova
31	Minas Gerais	3125200	Fama
31	Minas Gerais	3139003	Machado
31	Minas Gerais	3147204	Paraguacu
31	Minas Gerais	3151701	Poco Fundo
31	Minas Gerais	3166907	Serrania
31	Minas Gerais	3107109	Boa Esperanca
31	Minas Gerais	3110905	Campanha
31	Minas Gerais	3111309	Campo do Meio
31	Minas Gerais	3111606	Campos Gerais
31	Minas Gerais	3113909	Carmo da Cachoeira
31	Minas Gerais	3118700	Coqueiral
31	Minas Gerais	3123601	Eloi Mendes
31	Minas Gerais	3128105	Guape
31	Minas Gerais	3130507	Ilicinea
31	Minas Gerais	3142601	Monsenhor Paulo
31	Minas Gerais	3158300	Santana da Vargem
31	Minas Gerais	3160801	Sao Bento Abade
31	Minas Gerais	3165206	Sao Thome das Letras
31	Minas Gerais	3169307	Tres Coracoes
31	Minas Gerais	3169406	Tres Pontas
31	Minas Gerais	3170701	Varginha
31	Minas Gerais	3101409	Albertina
31	Minas Gerais	3102605	Andradas
31	Minas Gerais	3105301	Bandeira do Sul
31	Minas Gerais	3108404	Botelhos
31	Minas Gerais	3110301	Caldas
31	Minas Gerais	3111002	Campestre
31	Minas Gerais	3129905	Ibitiura de Minas
31	Minas Gerais	3130606	Inconfidentes
31	Minas Gerais	3134905	Jacutinga
31	Minas Gerais	3143401	Monte Siao
31	Minas Gerais	3146008	Ouro Fino
31	Minas Gerais	3151800	Pocos de Caldas
31	Minas Gerais	3159209	Santa Rita de Caldas
31	Minas Gerais	3107901	Bom Repouso
31	Minas Gerais	3108305	Borda da Mata
31	Minas Gerais	3109105	Bueno Brandao
31	Minas Gerais	3110509	Camanducaia
31	Minas Gerais	3110608	Cambui
31	Minas Gerais	3117900	Congonhal
31	Minas Gerais	3119906	Corrego do Bom Jesus
31	Minas Gerais	3124401	Espirito Santo do Dourado
31	Minas Gerais	3124500	Estiva
31	Minas Gerais	3125101	Extrema
31	Minas Gerais	3127404	Goncalves
31	Minas Gerais	3131505	Ipuiuna
31	Minas Gerais	3133600	Itapeva
31	Minas Gerais	3143807	Munhoz
31	Minas Gerais	3152501	Pouso Alegre
31	Minas Gerais	3165404	Sapucai-Mirim
31	Minas Gerais	3165578	Senador Amaral
31	Minas Gerais	3165800	Senador Jose Bento
31	Minas Gerais	3169059	Tocos do Moji
31	Minas Gerais	3169109	Toledo
31	Minas Gerais	3109709	Cachoeira de Minas
31	Minas Gerais	3113602	Careacu
31	Minas Gerais	3117207	Conceicao das Pedras
31	Minas Gerais	3117801	Conceicao dos Ouros
31	Minas Gerais	3119005	Cordislandia
31	Minas Gerais	3129202	Heliodora
31	Minas Gerais	3144409	Natercia
31	Minas Gerais	3149101	Pedralva
31	Minas Gerais	3159605	Santa Rita do Sapucai
31	Minas Gerais	3162005	Sao Goncalo do Sapucai
31	Minas Gerais	3162302	Sao Joao da Mata
31	Minas Gerais	3163201	Sao Jose do Alegre
31	Minas Gerais	3164407	Sao Sebastiao da Bela Vista
31	Minas Gerais	3167400	Silvianopolis
31	Minas Gerais	3169802	Turvolandia
31	Minas Gerais	3101300	Alagoa
31	Minas Gerais	3104908	Baependi
31	Minas Gerais	3110707	Cambuquira
31	Minas Gerais	3114105	Carmo de Minas
31	Minas Gerais	3115508	Caxambu
31	Minas Gerais	3117702	Conceicao do Rio Verde
31	Minas Gerais	3133006	Itamonte
31	Minas Gerais	3133105	Itanhandu
31	Minas Gerais	3135902	Jesuania
31	Minas Gerais	3137809	Lambari
31	Minas Gerais	3145505	Olimpio Noronha
31	Minas Gerais	3147600	Passa Quatro
31	Minas Gerais	3152600	Pouso Alto
31	Minas Gerais	3163706	Sao Lourenco
31	Minas Gerais	3164902	Sao Sebastiao do Rio Verde
31	Minas Gerais	3167806	Soledade de Minas
31	Minas Gerais	3101201	Aiuruoca
31	Minas Gerais	3102803	Andrelandia
31	Minas Gerais	3103603	Arantina
31	Minas Gerais	3107208	Bocaina de Minas
31	Minas Gerais	3107505	Bom Jardim de Minas
31	Minas Gerais	3114808	Carvalhos
31	Minas Gerais	3120805	Cruzilia
31	Minas Gerais	3138500	Liberdade
31	Minas Gerais	3141900	Minduri
31	Minas Gerais	3147808	Passa-Vinte
31	Minas Gerais	3165305	Sao Vicente de Minas
31	Minas Gerais	3166402	Seritinga
31	Minas Gerais	3167004	Serranos
31	Minas Gerais	3108909	Brasopolis
31	Minas Gerais	3118502	Consolacao
31	Minas Gerais	3120508	Cristina
31	Minas Gerais	3121100	Delfim Moreira
31	Minas Gerais	3122801	Dom Vicoso
31	Minas Gerais	3132404	Itajuba
31	Minas Gerais	3139904	Maria da Fe
31	Minas Gerais	3140407	Marmelopolis
31	Minas Gerais	3147303	Paraisopolis
31	Minas Gerais	3150901	Pirangucu
31	Minas Gerais	3151008	Piranguinho
31	Minas Gerais	3171709	Virginia
31	Minas Gerais	3172202	Wenceslau Braz
31	Minas Gerais	3114600	Carrancas
31	Minas Gerais	3130408	Ijaci
31	Minas Gerais	3130804	Ingai
31	Minas Gerais	3134301	Itumirim
31	Minas Gerais	3134509	Itutinga
31	Minas Gerais	3138203	Lavras
31	Minas Gerais	3138708	Luminarias
31	Minas Gerais	3144607	Nepomuceno
31	Minas Gerais	3154705	Ribeirao Vermelho
31	Minas Gerais	3115201	Conceicao da Barra de Minas
31	Minas Gerais	3119708	Coronel Xavier Chaves
31	Minas Gerais	3123007	Dores de Campos
31	Minas Gerais	3137403	Lagoa Dourada
31	Minas Gerais	3139102	Madre de Deus de Minas
31	Minas Gerais	3144508	Nazareno
31	Minas Gerais	3150307	Piedade do Rio Grande
31	Minas Gerais	3152709	Prados
31	Minas Gerais	3154200	Resende Costa
31	Minas Gerais	3156106	Ritapolis
31	Minas Gerais	3157336	Santa Cruz de Minas
31	Minas Gerais	3158706	Santana do Garambeu
31	Minas Gerais	3162500	Sao Joao del Rei
31	Minas Gerais	3165008	Sao Tiago
31	Minas Gerais	3168804	Tiradentes
31	Minas Gerais	3101631	Alfredo Vasconcelos
31	Minas Gerais	3102902	Antonio Carlos
31	Minas Gerais	3105608	Barbacena
31	Minas Gerais	3105905	Barroso
31	Minas Gerais	3112208	Capela Nova
31	Minas Gerais	3113107	Caranaiba
31	Minas Gerais	3113206	Carandai
31	Minas Gerais	3121506	Desterro do Melo
31	Minas Gerais	3129400	Ibertioga
31	Minas Gerais	3154408	Ressaquinha
31	Minas Gerais	3157302	Santa Barbara do Tugurio
31	Minas Gerais	3166204	Senhora dos Remedios
31	Minas Gerais	3100401	Acaiaca
31	Minas Gerais	3105707	Barra Longa
31	Minas Gerais	3122702	Dom Silverio
31	Minas Gerais	3128204	Guaraciaba
31	Minas Gerais	3135506	Jequeri
31	Minas Gerais	3145851	Oratorios
31	Minas Gerais	3150208	Piedade de Ponte Nova
31	Minas Gerais	3152105	Ponte Nova
31	Minas Gerais	3154002	Raul Soares
31	Minas Gerais	3154903	Rio Casca
31	Minas Gerais	3155009	Rio Doce
31	Minas Gerais	3157401	Santa Cruz do Escalvado
31	Minas Gerais	3160108	Santo Antonio do Grama
31	Minas Gerais	3164001	Sao Pedro dos Ferros
31	Minas Gerais	3165560	Sem-Peixe
31	Minas Gerais	3166303	Sericita
31	Minas Gerais	3170503	Urucania
31	Minas Gerais	3171154	Vermelho Novo
31	Minas Gerais	3100302	Abre Campo
31	Minas Gerais	3102050	Alto Caparao
31	Minas Gerais	3112109	Caparao
31	Minas Gerais	3112901	Caputira
31	Minas Gerais	3116001	Chale
31	Minas Gerais	3123528	Durande
31	Minas Gerais	3137700	Lajinha
31	Minas Gerais	3138674	Luisburgo
31	Minas Gerais	3139409	Manhuacu
31	Minas Gerais	3139508	Manhumirim
31	Minas Gerais	3140530	Martins Soares
31	Minas Gerais	3140902	Matipo
31	Minas Gerais	3148756	Pedra Bonita
31	Minas Gerais	3153509	Alto Jequitiba
31	Minas Gerais	3154150	Reduto
31	Minas Gerais	3157906	Santa Margarida
31	Minas Gerais	3158904	Santana do Manhuacu
31	Minas Gerais	3162559	Sao Joao do Manhuacu
31	Minas Gerais	3163607	Sao Jose do Mantimento
31	Minas Gerais	3167608	Simonesia
31	Minas Gerais	3102100	Alto Rio Doce
31	Minas Gerais	3102506	Amparo do Serra
31	Minas Gerais	3103702	Araponga
31	Minas Gerais	3108701	Bras Pires
31	Minas Gerais	3110202	Cajuri
31	Minas Gerais	3111705	Canaa
31	Minas Gerais	3116308	Cipotanea
31	Minas Gerais	3116704	Coimbra
31	Minas Gerais	3124005	Ervalia
31	Minas Gerais	3137908	Lamim
31	Minas Gerais	3148301	Paula Candido
31	Minas Gerais	3148806	Pedra do Anta
31	Minas Gerais	3150802	Piranga
31	Minas Gerais	3152303	Porto Firme
31	Minas Gerais	3153103	Presidente Bernardes
31	Minas Gerais	3155207	Rio Espera
31	Minas Gerais	3163805	Sao Miguel do Anta
31	Minas Gerais	3166006	Senhora de Oliveira
31	Minas Gerais	3168507	Teixeiras
31	Minas Gerais	3171303	Vicosa
31	Minas Gerais	3103108	Antonio Prado de Minas
31	Minas Gerais	3105509	Barao de Monte Alto
31	Minas Gerais	3110103	Caiana
31	Minas Gerais	3113305	Carangola
31	Minas Gerais	3122009	Divino
31	Minas Gerais	3124203	Espera Feliz
31	Minas Gerais	3124906	Eugenopolis
31	Minas Gerais	3125309	Faria Lemos
31	Minas Gerais	3125952	Fervedouro
31	Minas Gerais	3142106	Miradouro
31	Minas Gerais	3142205	Mirai
31	Minas Gerais	3143906	Muriae
31	Minas Gerais	3145877	Orizania
31	Minas Gerais	3148202	Patrocinio do Muriae
31	Minas Gerais	3149002	Pedra Dourada
31	Minas Gerais	3156452	Rosario da Limeira
31	Minas Gerais	3161403	Sao Francisco do Gloria
31	Minas Gerais	3164431	Sao Sebastiao da Vargem Alegre
31	Minas Gerais	3169208	Tombos
31	Minas Gerais	3171402	Vieiras
31	Minas Gerais	3104601	Astolfo Dutra
31	Minas Gerais	3121902	Divinesia
31	Minas Gerais	3123304	Dores do Turvo
31	Minas Gerais	3128402	Guarani
31	Minas Gerais	3128808	Guidoval
31	Minas Gerais	3129004	Guiricema
31	Minas Gerais	3141603	Merces
31	Minas Gerais	3151305	Pirauba
31	Minas Gerais	3155801	Rio Pomba
31	Minas Gerais	3156304	Rodeiro
31	Minas Gerais	3161502	Sao Geraldo
31	Minas Gerais	3165701	Senador Firmino
31	Minas Gerais	3167301	Silveirania
31	Minas Gerais	3167905	Tabuleiro
31	Minas Gerais	3169000	Tocantins
31	Minas Gerais	3169901	Uba
31	Minas Gerais	3172004	Visconde do Rio Branco
31	Minas Gerais	3103306	Aracitaba
31	Minas Gerais	3106101	Belmiro Braga
31	Minas Gerais	3106804	Bias Fortes
31	Minas Gerais	3106903	Bicas
31	Minas Gerais	3115904	Chacara
31	Minas Gerais	3116209	Chiador
31	Minas Gerais	3119609	Coronel Pacheco
31	Minas Gerais	3121308	Descoberto
31	Minas Gerais	3125002	Ewbank da Camara
31	Minas Gerais	3127388	Goiana
31	Minas Gerais	3128501	Guarara
31	Minas Gerais	3136702	Juiz de Fora
31	Minas Gerais	3138609	Lima Duarte
31	Minas Gerais	3139805	Mar de Espanha
31	Minas Gerais	3140209	Maripa de Minas
31	Minas Gerais	3140803	Matias Barbosa
31	Minas Gerais	3145406	Olaria
31	Minas Gerais	3145703	Oliveira Fortes
31	Minas Gerais	3146602	Paiva
31	Minas Gerais	3149408	Pedro Teixeira
31	Minas Gerais	3149507	Pequeri
31	Minas Gerais	3150109	Piau
31	Minas Gerais	3155405	Rio Novo
31	Minas Gerais	3155900	Rio Preto
31	Minas Gerais	3156205	Rochedo de Minas
31	Minas Gerais	3157278	Santa Barbara do Monte Verde
31	Minas Gerais	3158607	Santana do Deserto
31	Minas Gerais	3159308	Santa Rita de Jacutinga
31	Minas Gerais	3159407	Santa Rita de Ibitipoca
31	Minas Gerais	3160702	Santos Dumont
31	Minas Gerais	3162906	Sao Joao Nepomuceno
31	Minas Gerais	3165602	Senador Cortes
31	Minas Gerais	3167509	Simao Pereira
31	Minas Gerais	3101508	Alem Paraiba
31	Minas Gerais	3104403	Argirita
31	Minas Gerais	3115300	Cataguases
31	Minas Gerais	3122900	Dona Eusebia
31	Minas Gerais	3124609	Estrela Dalva
31	Minas Gerais	3132602	Itamarati de Minas
31	Minas Gerais	3138005	Laranjal
31	Minas Gerais	3138401	Leopoldina
31	Minas Gerais	3146701	Palma
31	Minas Gerais	3151107	Pirapetinga
31	Minas Gerais	3154101	Recreio
31	Minas Gerais	3158409	Santana de Cataguases
31	Minas Gerais	3160009	Santo Antonio do Aventureiro
31	Minas Gerais	3172103	Volta Grande
32	Espirito Santo	3200169	agua Doce do Norte
32	Espirito Santo	3200904	Barra de Sao Francisco
32	Espirito Santo	3202108	Ecoporanga
32	Espirito Santo	3203304	Mantenopolis
32	Espirito Santo	3200136	aguia Branca
32	Espirito Santo	3201001	Boa Esperanca
32	Espirito Santo	3203908	Nova Venecia
32	Espirito Santo	3204708	Sao Gabriel da Palha
32	Espirito Santo	3205150	Vila Pavao
32	Espirito Santo	3205176	Vila Valerio
32	Espirito Santo	3200359	Alto Rio Novo
32	Espirito Santo	3200805	Baixo Guandu
32	Espirito Santo	3201506	Colatina
32	Espirito Santo	3202256	Governador Lindenberg
32	Espirito Santo	3203353	Marilandia
32	Espirito Santo	3204005	Pancas
32	Espirito Santo	3204658	Sao Domingos do Norte
32	Espirito Santo	3203502	Montanha
32	Espirito Santo	3203601	Mucurici
32	Espirito Santo	3204104	Pinheiros
32	Espirito Santo	3204252	Ponto Belo
32	Espirito Santo	3201605	Conceicao da Barra
32	Espirito Santo	3203056	Jaguare
32	Espirito Santo	3204054	Pedro Canario
32	Espirito Santo	3204906	Sao Mateus
32	Espirito Santo	3200607	Aracruz
32	Espirito Santo	3202207	Fundao
32	Espirito Santo	3202504	Ibiracu
32	Espirito Santo	3203130	Joao Neiva
32	Espirito Santo	3203205	Linhares
32	Espirito Santo	3204351	Rio Bananal
32	Espirito Santo	3205010	Sooretama
32	Espirito Santo	3200102	Afonso Claudio
32	Espirito Santo	3201159	Brejetuba
32	Espirito Santo	3201704	Conceicao do Castelo
32	Espirito Santo	3201902	Domingos Martins
32	Espirito Santo	3203163	Laranja da Terra
32	Espirito Santo	3203346	Marechal Floriano
32	Espirito Santo	3205069	Venda Nova do Imigrante
32	Espirito Santo	3202702	Itaguacu
32	Espirito Santo	3202900	Itarana
32	Espirito Santo	3204500	Santa Leopoldina
32	Espirito Santo	3204559	Santa Maria de Jetiba
32	Espirito Santo	3204609	Santa Teresa
32	Espirito Santo	3204955	Sao Roque do Canaa
32	Espirito Santo	3201308	Cariacica
32	Espirito Santo	3205002	Serra
32	Espirito Santo	3205101	Viana
32	Espirito Santo	3205200	Vila Velha
32	Espirito Santo	3205309	Vitoria
32	Espirito Santo	3200300	Alfredo Chaves
32	Espirito Santo	3200409	Anchieta
32	Espirito Santo	3202405	Guarapari
32	Espirito Santo	3202603	Iconha
32	Espirito Santo	3204203	Piuma
32	Espirito Santo	3204401	Rio Novo do Sul
32	Espirito Santo	3200201	Alegre
32	Espirito Santo	3201803	Divino de Sao Lourenco
32	Espirito Santo	3202009	Dores do Rio Preto
32	Espirito Santo	3202306	Guacui
32	Espirito Santo	3202454	Ibatiba
32	Espirito Santo	3202553	Ibitirama
32	Espirito Santo	3202652	Irupi
32	Espirito Santo	3203007	Iuna
32	Espirito Santo	3203700	Muniz Freire
32	Espirito Santo	3200508	Apiaca
32	Espirito Santo	3200706	Atilio Vivacqua
32	Espirito Santo	3201100	Bom Jesus do Norte
32	Espirito Santo	3201209	Cachoeiro de Itapemirim
32	Espirito Santo	3201407	Castelo
32	Espirito Santo	3203106	Jeronimo Monteiro
32	Espirito Santo	3203403	Mimoso do Sul
32	Espirito Santo	3203809	Muqui
32	Espirito Santo	3204807	Sao Jose do Calcado
32	Espirito Santo	3205036	Vargem Alta
32	Espirito Santo	3202801	Itapemirim
32	Espirito Santo	3203320	Marataizes
32	Espirito Santo	3204302	Presidente Kennedy
33	Rio de Janeiro	3300605	Bom Jesus do Itabapoana
33	Rio de Janeiro	3302056	Italva
33	Rio de Janeiro	3302205	Itaperuna
33	Rio de Janeiro	3302304	Laje do Muriae
33	Rio de Janeiro	3303104	Natividade
33	Rio de Janeiro	3304102	Porciuncula
33	Rio de Janeiro	3306156	Varre-Sai
33	Rio de Janeiro	3300159	Aperibe
33	Rio de Janeiro	3300902	Cambuci
33	Rio de Janeiro	3302106	Itaocara
33	Rio de Janeiro	3303005	Miracema
33	Rio de Janeiro	3304706	Santo Antonio de Padua
33	Rio de Janeiro	3305133	Sao Jose de Uba
33	Rio de Janeiro	3301009	Campos dos Goytacazes
33	Rio de Janeiro	3301157	Cardoso Moreira
33	Rio de Janeiro	3304755	Sao Francisco de Itabapoana
33	Rio de Janeiro	3304805	Sao Fidelis
33	Rio de Janeiro	3305000	Sao Joao da Barra
33	Rio de Janeiro	3300936	Carapebus
33	Rio de Janeiro	3301405	Conceicao de Macabu
33	Rio de Janeiro	3302403	Macae
33	Rio de Janeiro	3304151	Quissama
33	Rio de Janeiro	3300225	Areal
33	Rio de Janeiro	3300951	Comendador Levy Gasparian
33	Rio de Janeiro	3303708	Paraiba do Sul
33	Rio de Janeiro	3305406	Sapucaia
33	Rio de Janeiro	3306008	Tres Rios
33	Rio de Janeiro	3301108	Cantagalo
33	Rio de Janeiro	3301207	Carmo
33	Rio de Janeiro	3301504	Cordeiro
33	Rio de Janeiro	3302452	Macuco
33	Rio de Janeiro	3300506	Bom Jardim
33	Rio de Janeiro	3301603	Duas Barras
33	Rio de Janeiro	3303401	Nova Friburgo
33	Rio de Janeiro	3305703	Sumidouro
33	Rio de Janeiro	3304607	Santa Maria Madalena
33	Rio de Janeiro	3305307	Sao Sebastiao do Alto
33	Rio de Janeiro	3305901	Trajano de Morais
33	Rio de Janeiro	3301306	Casimiro de Abreu
33	Rio de Janeiro	3304524	Rio das Ostras
33	Rio de Janeiro	3305604	Silva Jardim
33	Rio de Janeiro	3300209	Araruama
33	Rio de Janeiro	3300233	Armacao dos Buzios
33	Rio de Janeiro	3300258	Arraial do Cabo
33	Rio de Janeiro	3300704	Cabo Frio
33	Rio de Janeiro	3301876	Iguaba Grande
33	Rio de Janeiro	3305208	Sao Pedro da Aldeia
33	Rio de Janeiro	3305505	Saquarema
33	Rio de Janeiro	3300407	Barra Mansa
33	Rio de Janeiro	3302254	Itatiaia
33	Rio de Janeiro	3303955	Pinheiral
33	Rio de Janeiro	3304003	Pirai
33	Rio de Janeiro	3304110	Porto Real
33	Rio de Janeiro	3304128	Quatis
33	Rio de Janeiro	3304201	Resende
33	Rio de Janeiro	3304409	Rio Claro
33	Rio de Janeiro	3306305	Volta Redonda
33	Rio de Janeiro	3300308	Barra do Pirai
33	Rio de Janeiro	3304508	Rio das Flores
33	Rio de Janeiro	3306107	Valenca
33	Rio de Janeiro	3300100	Angra dos Reis
33	Rio de Janeiro	3303807	Parati
33	Rio de Janeiro	3301801	Engenheiro Paulo de Frontin
33	Rio de Janeiro	3302809	Mendes
33	Rio de Janeiro	3302908	Miguel Pereira
33	Rio de Janeiro	3303609	Paracambi
33	Rio de Janeiro	3303856	Paty do Alferes
33	Rio de Janeiro	3306206	Vassouras
33	Rio de Janeiro	3303906	Petropolis
33	Rio de Janeiro	3305158	Sao Jose do Vale do Rio Preto
33	Rio de Janeiro	3305802	Teresopolis
33	Rio de Janeiro	3300803	Cachoeiras de Macacu
33	Rio de Janeiro	3304300	Rio Bonito
33	Rio de Janeiro	3302007	Itaguai
33	Rio de Janeiro	3302601	Mangaratiba
33	Rio de Janeiro	3305554	Seropedica
33	Rio de Janeiro	3300456	Belford Roxo
33	Rio de Janeiro	3301702	Duque de Caxias
33	Rio de Janeiro	3301850	Guapimirim
33	Rio de Janeiro	3301900	Itaborai
33	Rio de Janeiro	3302270	Japeri
33	Rio de Janeiro	3302502	Mage
33	Rio de Janeiro	3302700	Marica
33	Rio de Janeiro	3302858	Mesquita
33	Rio de Janeiro	3303203	Nilopolis
33	Rio de Janeiro	3303302	Niteroi
33	Rio de Janeiro	3303500	Nova Iguacu
33	Rio de Janeiro	3304144	Queimados
33	Rio de Janeiro	3304557	Rio de Janeiro
33	Rio de Janeiro	3304904	Sao Goncalo
33	Rio de Janeiro	3305109	Sao Joao de Meriti
33	Rio de Janeiro	3305752	Tangua
35	Sao Paulo	3502606	Aparecida d'Oeste
35	Sao Paulo	3503950	Aspasia
35	Sao Paulo	3513850	Dirce Reis
35	Sao Paulo	3514205	Dolcinopolis
35	Sao Paulo	3524808	Jales
35	Sao Paulo	3529104	Marinopolis
35	Sao Paulo	3529658	Mesopolis
35	Sao Paulo	3532843	Nova Canaa Paulista
35	Sao Paulo	3535200	Palmeira d'Oeste
35	Sao Paulo	3535903	Paranapua
35	Sao Paulo	3540259	Pontalinda
35	Sao Paulo	3540408	Populina
35	Sao Paulo	3544509	Rubineia
35	Sao Paulo	3545704	Santa Albertina
35	Sao Paulo	3546108	Santa Clara d'Oeste
35	Sao Paulo	3546603	Santa Fe do Sul
35	Sao Paulo	3547205	Santana da Ponte Pensa
35	Sao Paulo	3547403	Santa Rita d'Oeste
35	Sao Paulo	3547650	Santa Salete
35	Sao Paulo	3549003	Sao Francisco
35	Sao Paulo	3554904	Tres Fronteiras
35	Sao Paulo	3555802	Urania
35	Sao Paulo	3556958	Vitoria Brasil
35	Sao Paulo	3515202	Estrela d'Oeste
35	Sao Paulo	3515509	Fernandopolis
35	Sao Paulo	3518008	Guarani d'Oeste
35	Sao Paulo	3520707	Indiapora
35	Sao Paulo	3528205	Macedonia
35	Sao Paulo	3529609	Meridiano
35	Sao Paulo	3530003	Mira Estrela
35	Sao Paulo	3534757	Ouroeste
35	Sao Paulo	3536901	Pedranopolis
35	Sao Paulo	3549201	Sao Joao das Duas Pontes
35	Sao Paulo	3555307	Turmalina
35	Sao Paulo	3501202	alvares Florence
35	Sao Paulo	3501806	Americo de Campos
35	Sao Paulo	3510708	Cardoso
35	Sao Paulo	3512902	Cosmorama
35	Sao Paulo	3536257	Parisi
35	Sao Paulo	3540309	Pontes Gestal
35	Sao Paulo	3544202	Riolandia
35	Sao Paulo	3556107	Valentim Gentil
35	Sao Paulo	3557105	Votuporanga
35	Sao Paulo	3500204	Adolfo
35	Sao Paulo	3500907	Altair
35	Sao Paulo	3504602	Bady Bassitt
35	Sao Paulo	3504800	Balsamo
35	Sao Paulo	3511300	Cedral
35	Sao Paulo	3517505	Guapiacu
35	Sao Paulo	3517901	Guaraci
35	Sao Paulo	3519402	Ibira
35	Sao Paulo	3519808	Icem
35	Sao Paulo	3521150	Ipigua
35	Sao Paulo	3524501	Jaci
35	Sao Paulo	3525706	Jose Bonifacio
35	Sao Paulo	3529500	Mendonca
35	Sao Paulo	3530300	Mirassol
35	Sao Paulo	3530409	Mirassolandia
35	Sao Paulo	3532801	Nova Alianca
35	Sao Paulo	3533007	Nova Granada
35	Sao Paulo	3533908	Olimpia
35	Sao Paulo	3534005	Onda Verde
35	Sao Paulo	3534203	Orindiuva
35	Sao Paulo	3535002	Palestina
35	Sao Paulo	3536604	Paulo de Faria
35	Sao Paulo	3539608	Planalto
35	Sao Paulo	3540804	Potirendaba
35	Sao Paulo	3549805	Sao Jose do Rio Preto
35	Sao Paulo	3553401	Tanabi
35	Sao Paulo	3555356	Ubarana
35	Sao Paulo	3555604	Uchoa
35	Sao Paulo	3557154	Zacarias
35	Sao Paulo	3503703	Ariranha
35	Sao Paulo	3509304	Cajobi
35	Sao Paulo	3511102	Catanduva
35	Sao Paulo	3511201	Catigua
35	Sao Paulo	3514924	Elisiario
35	Sao Paulo	3514957	Embauba
35	Sao Paulo	3533254	Novais
35	Sao Paulo	3535101	Palmares Paulista
35	Sao Paulo	3535705	Paraiso
35	Sao Paulo	3538105	Pindorama
35	Sao Paulo	3545605	Santa Adelia
35	Sao Paulo	3551900	Severinia
35	Sao Paulo	3552601	Tabapua
35	Sao Paulo	3504206	Auriflama
35	Sao Paulo	3515905	Floreal
35	Sao Paulo	3516804	Gastao Vidigal
35	Sao Paulo	3516903	General Salgado
35	Sao Paulo	3518909	Guzolandia
35	Sao Paulo	3528304	Magda
35	Sao Paulo	3532868	Nova Castilho
35	Sao Paulo	3533304	Nova Luzitania
35	Sao Paulo	3549250	Sao Joao de Iracema
35	Sao Paulo	3528106	Macaubal
35	Sao Paulo	3531001	Moncoes
35	Sao Paulo	3531407	Monte Aprazivel
35	Sao Paulo	3532504	Neves Paulista
35	Sao Paulo	3532603	Nhandeara
35	Sao Paulo	3532702	Nipoa
35	Sao Paulo	3539905	Poloni
35	Sao Paulo	3551306	Sebastianopolis do Sul
35	Sao Paulo	3555703	Uniao Paulista
35	Sao Paulo	3521507	Irapua
35	Sao Paulo	3521903	Itajobi
35	Sao Paulo	3528858	Marapoama
35	Sao Paulo	3533502	Novo Horizonte
35	Sao Paulo	3544806	Sales
35	Sao Paulo	3556008	Urupes
35	Sao Paulo	3505500	Barretos
35	Sao Paulo	3512001	Colina
35	Sao Paulo	3512100	Colombia
35	Sao Paulo	3517406	Guaira
35	Sao Paulo	3521309	Ipua
35	Sao Paulo	3524204	Jaborandi
35	Sao Paulo	3529708	Miguelopolis
35	Sao Paulo	3531902	Morro Agudo
35	Sao Paulo	3533601	Nuporanga
35	Sao Paulo	3534302	Orlandia
35	Sao Paulo	3544905	Sales Oliveira
35	Sao Paulo	3549409	Sao Joaquim da Barra
35	Sao Paulo	3503000	Aramina
35	Sao Paulo	3508207	Buritizal
35	Sao Paulo	3517703	Guara
35	Sao Paulo	3520103	Igarapava
35	Sao Paulo	3524105	Ituverava
35	Sao Paulo	3513207	Cristais Paulista
35	Sao Paulo	3516200	Franca
35	Sao Paulo	3523701	Itirapua
35	Sao Paulo	3525409	Jeriquara
35	Sao Paulo	3536307	Patrocinio Paulista
35	Sao Paulo	3537008	Pedregulho
35	Sao Paulo	3542701	Restinga
35	Sao Paulo	3543105	Ribeirao Corrente
35	Sao Paulo	3543600	Rifaina
35	Sao Paulo	3549508	Sao Jose da Bela Vista
35	Sao Paulo	3506102	Bebedouro
35	Sao Paulo	3510104	Candido Rodrigues
35	Sao Paulo	3515608	Fernando Prestes
35	Sao Paulo	3518602	Guariba
35	Sao Paulo	3524303	Jaboticabal
35	Sao Paulo	3531308	Monte Alto
35	Sao Paulo	3531506	Monte Azul Paulista
35	Sao Paulo	3539004	Pirangi
35	Sao Paulo	3539509	Pitangueiras
35	Sao Paulo	3546504	Santa Ernestina
35	Sao Paulo	3553104	Taiacu
35	Sao Paulo	3553203	Taiuva
35	Sao Paulo	3553658	Taquaral
35	Sao Paulo	3553708	Taquaritinga
35	Sao Paulo	3554409	Terra Roxa
35	Sao Paulo	3556800	Viradouro
35	Sao Paulo	3556909	Vista Alegre do Alto
35	Sao Paulo	3505609	Barrinha
35	Sao Paulo	3507803	Brodowski
35	Sao Paulo	3513108	Cravinhos
35	Sao Paulo	3514601	Dumont
35	Sao Paulo	3518859	Guatapara
35	Sao Paulo	3525102	Jardinopolis
35	Sao Paulo	3527603	Luis Antonio
35	Sao Paulo	3540200	Pontal
35	Sao Paulo	3540903	Pradopolis
35	Sao Paulo	3543402	Ribeirao Preto
35	Sao Paulo	3547502	Santa Rita do Passa Quatro
35	Sao Paulo	3547601	Santa Rosa de Viterbo
35	Sao Paulo	3550902	Sao Simao
35	Sao Paulo	3551405	Serra Azul
35	Sao Paulo	3551504	Serrana
35	Sao Paulo	3551702	Sertaozinho
35	Sao Paulo	3501004	Altinopolis
35	Sao Paulo	3505906	Batatais
35	Sao Paulo	3509403	Cajuru
35	Sao Paulo	3510906	Cassia dos Coqueiros
35	Sao Paulo	3546256	Santa Cruz da Esperanca
35	Sao Paulo	3547908	Santo Antonio da Alegria
35	Sao Paulo	3502101	Andradina
35	Sao Paulo	3511003	Castilho
35	Sao Paulo	3517802	Guaracai
35	Sao Paulo	3520442	Ilha Solteira
35	Sao Paulo	3523008	Itapura
35	Sao Paulo	3530102	Mirandopolis
35	Sao Paulo	3532108	Murutinga do Sul
35	Sao Paulo	3533205	Nova Independencia
35	Sao Paulo	3537404	Pereira Barreto
35	Sao Paulo	3552304	Sud Mennucci
35	Sao Paulo	3552551	Suzanapolis
35	Sao Paulo	3502804	Aracatuba
35	Sao Paulo	3506201	Bento de Abreu
35	Sao Paulo	3518206	Guararapes
35	Sao Paulo	3526506	Lavinia
35	Sao Paulo	3544400	Rubiacea
35	Sao Paulo	3548054	Santo Antonio do Aracangua
35	Sao Paulo	3556305	Valparaiso
35	Sao Paulo	3501103	Alto Alegre
35	Sao Paulo	3504404	Avanhandava
35	Sao Paulo	3505104	Barbosa
35	Sao Paulo	3506409	Bilac
35	Sao Paulo	3506508	Birigui
35	Sao Paulo	3507704	Brauna
35	Sao Paulo	3507753	Brejo Alegre
35	Sao Paulo	3508108	Buritama
35	Sao Paulo	3511904	Clementina
35	Sao Paulo	3512506	Coroados
35	Sao Paulo	3516507	Gabriel Monteiro
35	Sao Paulo	3517109	Glicerio
35	Sao Paulo	3527256	Lourdes
35	Sao Paulo	3527702	Luiziania
35	Sao Paulo	3537305	Penapolis
35	Sao Paulo	3537701	Piacatu
35	Sao Paulo	3548401	Santopolis do Aguapei
35	Sao Paulo	3555208	Turiuba
35	Sao Paulo	3508801	Cafelandia
35	Sao Paulo	3517000	Getulina
35	Sao Paulo	3517208	Guaicara
35	Sao Paulo	3517307	Guaimbe
35	Sao Paulo	3525805	Julio Mesquita
35	Sao Paulo	3527108	Lins
35	Sao Paulo	3541604	Promissao
35	Sao Paulo	3544608	Sabino
35	Sao Paulo	3500709	Agudos
35	Sao Paulo	3503406	Arealva
35	Sao Paulo	3503604	Areiopolis
35	Sao Paulo	3504305	Avai
35	Sao Paulo	3504701	Balbinos
35	Sao Paulo	3506003	Bauru
35	Sao Paulo	3507456	Borebi
35	Sao Paulo	3508306	Cabralia Paulista
35	Sao Paulo	3514502	Duartina
35	Sao Paulo	3518107	Guaranta
35	Sao Paulo	3519105	Iacanga
35	Sao Paulo	3526803	Lencois Paulista
35	Sao Paulo	3527504	Lucianopolis
35	Sao Paulo	3536570	Paulistania
35	Sao Paulo	3538907	Pirajui
35	Sao Paulo	3539400	Piratininga
35	Sao Paulo	3540101	Pongai
35	Sao Paulo	3541109	Presidente Alves
35	Sao Paulo	3542503	Reginopolis
35	Sao Paulo	3555505	Ubirajara
35	Sao Paulo	3555901	Uru
35	Sao Paulo	3505203	Bariri
35	Sao Paulo	3505302	Barra Bonita
35	Sao Paulo	3506805	Bocaina
35	Sao Paulo	3507308	Boraceia
35	Sao Paulo	3514106	Dois Corregos
35	Sao Paulo	3520004	Igaracu do Tiete
35	Sao Paulo	3522000	Itaju
35	Sao Paulo	3522901	Itapui
35	Sao Paulo	3525300	Jau
35	Sao Paulo	3528007	Macatuba
35	Sao Paulo	3529807	Mineiros do Tiete
35	Sao Paulo	3536703	Pederneiras
35	Sao Paulo	3500550	aguas de Santa Barbara
35	Sao Paulo	3503109	Arandu
35	Sao Paulo	3504503	Avare
35	Sao Paulo	3511409	Cerqueira Cesar
35	Sao Paulo	3519253	Iaras
35	Sao Paulo	3521804	Itai
35	Sao Paulo	3523503	Itatinga
35	Sao Paulo	3535804	Paranapanema
35	Sao Paulo	3502309	Anhembi
35	Sao Paulo	3506904	Bofete
35	Sao Paulo	3507506	Botucatu
35	Sao Paulo	3512308	Conchas
35	Sao Paulo	3536109	Pardinho
35	Sao Paulo	3541059	Pratania
35	Sao Paulo	3550100	Sao Manuel
35	Sao Paulo	3501707	Americo Brasiliense
35	Sao Paulo	3503208	Araraquara
35	Sao Paulo	3506706	Boa Esperanca do Sul
35	Sao Paulo	3507407	Borborema
35	Sao Paulo	3514007	Dobrada
35	Sao Paulo	3516853	Gaviao Peixoto
35	Sao Paulo	3519600	Ibitinga
35	Sao Paulo	3522703	Itapolis
35	Sao Paulo	3529302	Matao
35	Sao Paulo	3532058	Motuca
35	Sao Paulo	3532900	Nova Europa
35	Sao Paulo	3543709	Rincao
35	Sao Paulo	3546900	Santa Lucia
35	Sao Paulo	3552700	Tabatinga
35	Sao Paulo	3554755	Trabiju
35	Sao Paulo	3502002	Analandia
35	Sao Paulo	3513702	Descalvado
35	Sao Paulo	3514304	Dourado
35	Sao Paulo	3519303	Ibate
35	Sao Paulo	3542909	Ribeirao Bonito
35	Sao Paulo	3548906	Sao Carlos
35	Sao Paulo	3507902	Brotas
35	Sao Paulo	3512704	Corumbatai
35	Sao Paulo	3521101	Ipeuna
35	Sao Paulo	3523602	Itirapina
35	Sao Paulo	3543907	Rio Claro
35	Sao Paulo	3554706	Torrinha
35	Sao Paulo	3503307	Araras
35	Sao Paulo	3512209	Conchal
35	Sao Paulo	3512407	Cordeiropolis
35	Sao Paulo	3521408	Iracemapolis
35	Sao Paulo	3526704	Leme
35	Sao Paulo	3526902	Limeira
35	Sao Paulo	3546207	Santa Cruz da Conceicao
35	Sao Paulo	3546702	Santa Gertrudes
35	Sao Paulo	3500600	aguas de Sao Pedro
35	Sao Paulo	3510401	Capivari
35	Sao Paulo	3511706	Charqueada
35	Sao Paulo	3525854	Jumirim
35	Sao Paulo	3530904	Mombuca
35	Sao Paulo	3538709	Piracicaba
35	Sao Paulo	3542107	Rafard
35	Sao Paulo	3544004	Rio das Pedras
35	Sao Paulo	3545159	Saltinho
35	Sao Paulo	3547007	Santa Maria da Serra
35	Sao Paulo	3550407	Sao Pedro
35	Sao Paulo	3554508	Tiete
35	Sao Paulo	3500303	Aguai
35	Sao Paulo	3539301	Pirassununga
35	Sao Paulo	3540705	Porto Ferreira
35	Sao Paulo	3546306	Santa Cruz das Palmeiras
35	Sao Paulo	3500402	aguas da Prata
35	Sao Paulo	3508702	Caconde
35	Sao Paulo	3510807	Casa Branca
35	Sao Paulo	3513900	Divinolandia
35	Sao Paulo	3515186	Espirito Santo do Pinhal
35	Sao Paulo	3523800	Itobi
35	Sao Paulo	3530508	Mococa
35	Sao Paulo	3548104	Santo Antonio do Jardim
35	Sao Paulo	3549102	Sao Joao da Boa Vista
35	Sao Paulo	3549706	Sao Jose do Rio Pardo
35	Sao Paulo	3550803	Sao Sebastiao da Grama
35	Sao Paulo	3553302	Tambau
35	Sao Paulo	3553609	Tapiratiba
35	Sao Paulo	3556404	Vargem Grande do Sul
35	Sao Paulo	3503802	Artur Nogueira
35	Sao Paulo	3515152	Engenheiro Coelho
35	Sao Paulo	3522604	Itapira
35	Sao Paulo	3530706	Mogi Guacu
35	Sao Paulo	3530805	Moji Mirim
35	Sao Paulo	3548005	Santo Antonio de Posse
35	Sao Paulo	3557303	Estiva Gerbi
35	Sao Paulo	3501608	Americana
35	Sao Paulo	3509502	Campinas
35	Sao Paulo	3512803	Cosmopolis
35	Sao Paulo	3514908	Elias Fausto
35	Sao Paulo	3519055	Holambra
35	Sao Paulo	3519071	Hortolandia
35	Sao Paulo	3520509	Indaiatuba
35	Sao Paulo	3524709	Jaguariuna
35	Sao Paulo	3531803	Monte Mor
35	Sao Paulo	3533403	Nova Odessa
35	Sao Paulo	3536505	Paulinia
35	Sao Paulo	3537107	Pedreira
35	Sao Paulo	3545803	Santa Barbara d'Oeste
35	Sao Paulo	3552403	Sumare
35	Sao Paulo	3556206	Valinhos
35	Sao Paulo	3556701	Vinhedo
35	Sao Paulo	3500501	aguas de Lindoia
35	Sao Paulo	3501905	Amparo
35	Sao Paulo	3527009	Lindoia
35	Sao Paulo	3531209	Monte Alegre do Sul
35	Sao Paulo	3536802	Pedra Bela
35	Sao Paulo	3538204	Pinhalzinho
35	Sao Paulo	3551603	Serra Negra
35	Sao Paulo	3552106	Socorro
35	Sao Paulo	3514403	Dracena
35	Sao Paulo	3526001	Junqueiropolis
35	Sao Paulo	3531605	Monte Castelo
35	Sao Paulo	3533106	Nova Guataporanga
35	Sao Paulo	3534807	Ouro Verde
35	Sao Paulo	3535408	Panorama
35	Sao Paulo	3536406	Pauliceia
35	Sao Paulo	3547106	Santa Mercedes
35	Sao Paulo	3549300	Sao Joao do Pau d'Alho
35	Sao Paulo	3555109	Tupi Paulista
35	Sao Paulo	3500105	Adamantina
35	Sao Paulo	3515806	Flora Rica
35	Sao Paulo	3516002	Florida Paulista
35	Sao Paulo	3520806	Inubia Paulista
35	Sao Paulo	3521606	Irapuru
35	Sao Paulo	3527405	Lucelia
35	Sao Paulo	3528908	Mariapolis
35	Sao Paulo	3534609	Osvaldo Cruz
35	Sao Paulo	3534906	Pacaembu
35	Sao Paulo	3536000	Parapua
35	Sao Paulo	3540853	Pracinha
35	Sao Paulo	3543808	Rinopolis
35	Sao Paulo	3544707	Sagres
35	Sao Paulo	3545100	Salmourao
35	Sao Paulo	3500808	Alfredo Marcondes
35	Sao Paulo	3501301	alvares Machado
35	Sao Paulo	3502408	Anhumas
35	Sao Paulo	3508900	Caiabu
35	Sao Paulo	3509106	Caiua
35	Sao Paulo	3515129	Emilianopolis
35	Sao Paulo	3515301	Estrela do Norte
35	Sao Paulo	3515350	Euclides da Cunha Paulista
35	Sao Paulo	3520608	Indiana
35	Sao Paulo	3525607	Joao Ramalho
35	Sao Paulo	3528700	Maraba Paulista
35	Sao Paulo	3529203	Martinopolis
35	Sao Paulo	3530201	Mirante do Paranapanema
35	Sao Paulo	3532207	Narandiba
35	Sao Paulo	3538303	Piquerobi
35	Sao Paulo	3539202	Pirapozinho
35	Sao Paulo	3541208	Presidente Bernardes
35	Sao Paulo	3541307	Presidente Epitacio
35	Sao Paulo	3541406	Presidente Prudente
35	Sao Paulo	3541505	Presidente Venceslau
35	Sao Paulo	3542206	Rancharia
35	Sao Paulo	3542404	Regente Feijo
35	Sao Paulo	3543238	Ribeirao dos indios
35	Sao Paulo	3544251	Rosana
35	Sao Paulo	3545506	Sandovalina
35	Sao Paulo	3547700	Santo Anastacio
35	Sao Paulo	3548302	Santo Expedito
35	Sao Paulo	3552908	Taciba
35	Sao Paulo	3553906	Tarabai
35	Sao Paulo	3554300	Teodoro Sampaio
35	Sao Paulo	3503356	Arco-iris
35	Sao Paulo	3505807	Bastos
35	Sao Paulo	3519006	Herculandia
35	Sao Paulo	3519204	Iacri
35	Sao Paulo	3541802	Queiroz
35	Sao Paulo	3542008	Quintana
35	Sao Paulo	3555000	Tupa
35	Sao Paulo	3501400	alvaro de Carvalho
35	Sao Paulo	3501509	Alvinlandia
35	Sao Paulo	3514700	Echapora
35	Sao Paulo	3515657	Fernao
35	Sao Paulo	3516606	Galia
35	Sao Paulo	3516705	Garca
35	Sao Paulo	3527801	Lupercio
35	Sao Paulo	3529005	Marilia
35	Sao Paulo	3533700	Ocaucu
35	Sao Paulo	3534104	Oriente
35	Sao Paulo	3534500	Oscar Bressane
35	Sao Paulo	3540002	Pompeia
35	Sao Paulo	3556602	Vera Cruz
35	Sao Paulo	3504008	Assis
35	Sao Paulo	3507209	Bora
35	Sao Paulo	3509809	Campos Novos Paulista
35	Sao Paulo	3510005	Candido Mota
35	Sao Paulo	3513306	Cruzalia
35	Sao Paulo	3516101	Florinia
35	Sao Paulo	3519501	Ibirarema
35	Sao Paulo	3519907	Iepe
35	Sao Paulo	3527900	Lutecia
35	Sao Paulo	3528809	Maracai
35	Sao Paulo	3532157	Nantes
35	Sao Paulo	3535309	Palmital
35	Sao Paulo	3535507	Paraguacu Paulista
35	Sao Paulo	3537156	Pedrinhas Paulista
35	Sao Paulo	3539707	Platina
35	Sao Paulo	3541703	Quata
35	Sao Paulo	3553955	Taruma
35	Sao Paulo	3506300	Bernardino de Campos
35	Sao Paulo	3510153	Canitar
35	Sao Paulo	3515194	Espirito Santo do Turvo
35	Sao Paulo	3515400	Fartura
35	Sao Paulo	3520905	Ipaussu
35	Sao Paulo	3528601	Manduri
35	Sao Paulo	3533809	oleo
35	Sao Paulo	3534708	Ourinhos
35	Sao Paulo	3538808	Piraju
35	Sao Paulo	3543204	Ribeirao do Sul
35	Sao Paulo	3545407	Salto Grande
35	Sao Paulo	3546405	Santa Cruz do Rio Pardo
35	Sao Paulo	3550506	Sao Pedro do Turvo
35	Sao Paulo	3551207	Sarutaia
35	Sao Paulo	3553005	Taguai
35	Sao Paulo	3554201	Tejupa
35	Sao Paulo	3554607	Timburi
35	Sao Paulo	3557204	Chavantes
35	Sao Paulo	3505005	Barao de Antonina
35	Sao Paulo	3507159	Bom Sucesso de Itarare
35	Sao Paulo	3508009	Buri
35	Sao Paulo	3512605	Coronel Macedo
35	Sao Paulo	3521705	Itabera
35	Sao Paulo	3522406	Itapeva
35	Sao Paulo	3522802	Itaporanga
35	Sao Paulo	3523206	Itarare
35	Sao Paulo	3532827	Nova Campina
35	Sao Paulo	3543501	Riversul
35	Sao Paulo	3553807	Taquarituba
35	Sao Paulo	3553856	Taquarivai
35	Sao Paulo	3500758	Alambari
35	Sao Paulo	3502200	Angatuba
35	Sao Paulo	3509452	Campina do Monte Alegre
35	Sao Paulo	3518503	Guarei
35	Sao Paulo	3522307	Itapetininga
35	Sao Paulo	3507001	Boituva
35	Sao Paulo	3511508	Cerquilho
35	Sao Paulo	3511607	Cesario Lange
35	Sao Paulo	3526407	Laranjal Paulista
35	Sao Paulo	3537503	Pereiras
35	Sao Paulo	3540507	Porangaba
35	Sao Paulo	3541653	Quadra
35	Sao Paulo	3554003	Tatui
35	Sao Paulo	3554656	Torre de Pedra
35	Sao Paulo	3502705	Apiai
35	Sao Paulo	3505351	Barra do Chapeu
35	Sao Paulo	3510203	Capao Bonito
35	Sao Paulo	3517604	Guapiara
35	Sao Paulo	3521200	Iporanga
35	Sao Paulo	3522158	Itaoca
35	Sao Paulo	3522653	Itapirapua Paulista
35	Sao Paulo	3542800	Ribeira
35	Sao Paulo	3543006	Ribeirao Branco
35	Sao Paulo	3543253	Ribeirao Grande
35	Sao Paulo	3519709	Ibiuna
35	Sao Paulo	3537800	Piedade
35	Sao Paulo	3537909	Pilar do Sul
35	Sao Paulo	3550209	Sao Miguel Arcanjo
35	Sao Paulo	3553500	Tapirai
35	Sao Paulo	3501152	Aluminio
35	Sao Paulo	3502754	Aracariguama
35	Sao Paulo	3502903	Aracoiaba da Serra
35	Sao Paulo	3508405	Cabreuva
35	Sao Paulo	3510302	Capela do Alto
35	Sao Paulo	3521002	Ipero
35	Sao Paulo	3523909	Itu
35	Sao Paulo	3528403	Mairinque
35	Sao Paulo	3540606	Porto Feliz
35	Sao Paulo	3545209	Salto
35	Sao Paulo	3545308	Salto de Pirapora
35	Sao Paulo	3550605	Sao Roque
35	Sao Paulo	3551108	Sarapui
35	Sao Paulo	3552205	Sorocaba
35	Sao Paulo	3557006	Votorantim
35	Sao Paulo	3509601	Campo Limpo Paulista
35	Sao Paulo	3524006	Itupeva
35	Sao Paulo	3525904	Jundiai
35	Sao Paulo	3527306	Louveira
35	Sao Paulo	3556503	Varzea Paulista
35	Sao Paulo	3504107	Atibaia
35	Sao Paulo	3507100	Bom Jesus dos Perdoes
35	Sao Paulo	3507605	Braganca Paulista
35	Sao Paulo	3523404	Itatiba
35	Sao Paulo	3525201	Jarinu
35	Sao Paulo	3525508	Joanopolis
35	Sao Paulo	3532009	Morungaba
35	Sao Paulo	3532405	Nazare Paulista
35	Sao Paulo	3538600	Piracaia
35	Sao Paulo	3554953	Tuiuti
35	Sao Paulo	3556354	Vargem
35	Sao Paulo	3509700	Campos do Jordao
35	Sao Paulo	3531704	Monteiro Lobato
35	Sao Paulo	3548203	Santo Antonio do Pinhal
35	Sao Paulo	3548609	Sao Bento do Sapucai
35	Sao Paulo	3508504	Cacapava
35	Sao Paulo	3520202	Igarata
35	Sao Paulo	3524402	Jacarei
35	Sao Paulo	3538006	Pindamonhangaba
35	Sao Paulo	3546009	Santa Branca
35	Sao Paulo	3549904	Sao Jose dos Campos
35	Sao Paulo	3554102	Taubate
35	Sao Paulo	3554805	Tremembe
35	Sao Paulo	3502507	Aparecida
35	Sao Paulo	3508603	Cachoeira Paulista
35	Sao Paulo	3509957	Canas
35	Sao Paulo	3513405	Cruzeiro
35	Sao Paulo	3518404	Guaratingueta
35	Sao Paulo	3526605	Lavrinhas
35	Sao Paulo	3527207	Lorena
35	Sao Paulo	3538501	Piquete
35	Sao Paulo	3540754	Potim
35	Sao Paulo	3541901	Queluz
35	Sao Paulo	3544301	Roseira
35	Sao Paulo	3503158	Arapei
35	Sao Paulo	3503505	Areias
35	Sao Paulo	3504909	Bananal
35	Sao Paulo	3549607	Sao Jose do Barreiro
35	Sao Paulo	3552007	Silveiras
35	Sao Paulo	3513603	Cunha
35	Sao Paulo	3524907	Jambeiro
35	Sao Paulo	3526308	Lagoinha
35	Sao Paulo	3532306	Natividade da Serra
35	Sao Paulo	3535606	Paraibuna
35	Sao Paulo	3542305	Redencao da Serra
35	Sao Paulo	3550001	Sao Luis do Paraitinga
35	Sao Paulo	3510500	Caraguatatuba
35	Sao Paulo	3520400	Ilhabela
35	Sao Paulo	3550704	Sao Sebastiao
35	Sao Paulo	3555406	Ubatuba
35	Sao Paulo	3505401	Barra do Turvo
35	Sao Paulo	3509254	Cajati
35	Sao Paulo	3509908	Cananeia
35	Sao Paulo	3514809	Eldorado
35	Sao Paulo	3520301	Iguape
35	Sao Paulo	3520426	Ilha Comprida
35	Sao Paulo	3524600	Jacupiranga
35	Sao Paulo	3526100	Juquia
35	Sao Paulo	3529906	Miracatu
35	Sao Paulo	3536208	Pariquera-Acu
35	Sao Paulo	3542602	Registro
35	Sao Paulo	3551801	Sete Barras
35	Sao Paulo	3522109	Itanhaem
35	Sao Paulo	3523305	Itariri
35	Sao Paulo	3531100	Mongagua
35	Sao Paulo	3537206	Pedro de Toledo
35	Sao Paulo	3537602	Peruibe
35	Sao Paulo	3505708	Barueri
35	Sao Paulo	3509205	Cajamar
35	Sao Paulo	3510609	Carapicuiba
35	Sao Paulo	3522505	Itapevi
35	Sao Paulo	3525003	Jandira
35	Sao Paulo	3534401	Osasco
35	Sao Paulo	3539103	Pirapora do Bom Jesus
35	Sao Paulo	3547304	Santana de Parnaiba
35	Sao Paulo	3509007	Caieiras
35	Sao Paulo	3516309	Francisco Morato
35	Sao Paulo	3516408	Franco da Rocha
35	Sao Paulo	3528502	Mairipora
35	Sao Paulo	3503901	Aruja
35	Sao Paulo	3518800	Guarulhos
35	Sao Paulo	3546801	Santa Isabel
35	Sao Paulo	3513009	Cotia
35	Sao Paulo	3515004	Embu
35	Sao Paulo	3515103	Embu-Guacu
35	Sao Paulo	3522208	Itapecerica da Serra
35	Sao Paulo	3526209	Juquitiba
35	Sao Paulo	3549953	Sao Lourenco da Serra
35	Sao Paulo	3552809	Taboao da Serra
35	Sao Paulo	3556453	Vargem Grande Paulista
35	Sao Paulo	3513801	Diadema
35	Sao Paulo	3529401	Maua
35	Sao Paulo	3543303	Ribeirao Pires
35	Sao Paulo	3544103	Rio Grande da Serra
35	Sao Paulo	3547809	Santo Andre
35	Sao Paulo	3548708	Sao Bernardo do Campo
35	Sao Paulo	3548807	Sao Caetano do Sul
35	Sao Paulo	3550308	Sao Paulo
35	Sao Paulo	3506607	Biritiba-Mirim
35	Sao Paulo	3515707	Ferraz de Vasconcelos
35	Sao Paulo	3518305	Guararema
35	Sao Paulo	3523107	Itaquaquecetuba
35	Sao Paulo	3530607	Mogi das Cruzes
35	Sao Paulo	3539806	Poa
35	Sao Paulo	3545001	Salesopolis
35	Sao Paulo	3552502	Suzano
35	Sao Paulo	3506359	Bertioga
35	Sao Paulo	3513504	Cubatao
35	Sao Paulo	3518701	Guaruja
35	Sao Paulo	3541000	Praia Grande
35	Sao Paulo	3548500	Santos
35	Sao Paulo	3551009	Sao Vicente
41	Parana	4100608	Alto Parana
41	Parana	4100905	Amapora
41	Parana	4106704	Cruzeiro do Sul
41	Parana	4107108	Diamante do Norte
41	Parana	4108908	Guairaca
41	Parana	4110300	Inaja
41	Parana	4111308	Itauna do Sul
41	Parana	4112603	Jardim Olinda
41	Parana	4113502	Loanda
41	Parana	4115002	Marilena
41	Parana	4115903	Mirador
41	Parana	4116505	Nova Alianca do Ivai
41	Parana	4117107	Nova Londrina
41	Parana	4118006	Paraiso do Norte
41	Parana	4118105	Paranacity
41	Parana	4118303	Paranapoema
41	Parana	4118402	Paranavai
41	Parana	4119707	Planaltina do Parana
41	Parana	4120200	Porto Rico
41	Parana	4121000	Querencia do Norte
41	Parana	4123303	Santa Cruz de Monte Castelo
41	Parana	4123709	Santa Isabel do Ivai
41	Parana	4123956	Santa Monica
41	Parana	4124202	Santo Antonio do Caiua
41	Parana	4124608	Sao Carlos do Ivai
41	Parana	4124905	Sao Joao do Caiua
41	Parana	4125902	Sao Pedro do Parana
41	Parana	4126702	Tamboara
41	Parana	4127304	Terra Rica
41	Parana	4100509	Altonia
41	Parana	4100707	Alto Piquiri
41	Parana	4103370	Brasilandia do Sul
41	Parana	4103479	Cafezal do Sul
41	Parana	4106605	Cruzeiro do Oeste
41	Parana	4107256	Douradina
41	Parana	4107520	Esperanca Nova
41	Parana	4108320	Francisco Alves
41	Parana	4109906	Icaraima
41	Parana	4110607	Ipora
41	Parana	4111555	Ivate
41	Parana	4114708	Maria Helena
41	Parana	4115101	Mariluz
41	Parana	4117206	Nova Olimpia
41	Parana	4118857	Perobal
41	Parana	4118907	Perola
41	Parana	4125357	Sao Jorge do Patrocinio
41	Parana	4126900	Tapira
41	Parana	4128104	Umuarama
41	Parana	4128625	Alto Paraiso
41	Parana	4128807	Xambre
41	Parana	4105508	Cianorte
41	Parana	4105607	Cidade Gaucha
41	Parana	4109104	Guaporema
41	Parana	4110409	Indianopolis
41	Parana	4112405	Japura
41	Parana	4113007	Jussara
41	Parana	4122602	Rondon
41	Parana	4125555	Sao Manoel do Parana
41	Parana	4126108	Sao Tome
41	Parana	4126801	Tapejara
41	Parana	4127908	Tuneiras do Oeste
41	Parana	4100459	Altamira do Parana
41	Parana	4103008	Boa Esperanca
41	Parana	4103909	Campina da Lagoa
41	Parana	4108601	Goioere
41	Parana	4112207	Janiopolis
41	Parana	4112959	Juranda
41	Parana	4116109	Moreira Sales
41	Parana	4116802	Nova Cantu
41	Parana	4120655	Quarto Centenario
41	Parana	4121356	Rancho Alegre D'Oeste
41	Parana	4128005	Ubirata
41	Parana	4101705	Araruna
41	Parana	4102505	Barbosa Ferraz
41	Parana	4104303	Campo Mourao
41	Parana	4106555	Corumbatai do Sul
41	Parana	4107504	Engenheiro Beltrao
41	Parana	4107553	Farol
41	Parana	4107702	Fenix
41	Parana	4110805	Iretama
41	Parana	4113734	Luiziana
41	Parana	4114005	Mambore
41	Parana	4118808	Peabiru
41	Parana	4121109	Quinta do Sol
41	Parana	4122503	Roncador
41	Parana	4127205	Terra Boa
41	Parana	4101150	angulo
41	Parana	4102109	Astorga
41	Parana	4102208	Atalaia
41	Parana	4103404	Cafeara
41	Parana	4105102	Centenario do Sul
41	Parana	4105904	Colorado
41	Parana	4108106	Florida
41	Parana	4109203	Guaraci
41	Parana	4110003	Iguaracu
41	Parana	4110904	Itaguaje
41	Parana	4111902	Jaguapita
41	Parana	4113601	Lobato
41	Parana	4113809	Lupionopolis
41	Parana	4114104	Mandaguacu
41	Parana	4116307	Munhoz de Melo
41	Parana	4116406	Nossa Senhora das Gracas
41	Parana	4116901	Nova Esperanca
41	Parana	4120408	Presidente Castelo Branco
41	Parana	4123402	Santa Fe
41	Parana	4123600	Santa Ines
41	Parana	4124509	Santo Inacio
41	Parana	4128302	Uniflor
41	Parana	4100806	Alvorada do Sul
41	Parana	4102802	Bela Vista do Paraiso
41	Parana	4108007	Florestopolis
41	Parana	4116000	Miraselva
41	Parana	4120002	Porecatu
41	Parana	4120333	Prado Ferreira
41	Parana	4120507	Primeiro de Maio
41	Parana	4126504	Sertanopolis
41	Parana	4107306	Doutor Camargo
41	Parana	4107801	Florai
41	Parana	4107900	Floresta
41	Parana	4111100	Itambe
41	Parana	4111605	Ivatuba
41	Parana	4117404	Ourizona
41	Parana	4125308	Sao Jorge do Ivai
41	Parana	4114203	Mandaguari
41	Parana	4114807	Marialva
41	Parana	4115200	Maringa
41	Parana	4117503	Paicandu
41	Parana	4126256	Sarandi
41	Parana	4101408	Apucarana
41	Parana	4101507	Arapongas
41	Parana	4103503	California
41	Parana	4103800	Cambira
41	Parana	4112108	Jandaia do Sul
41	Parana	4114906	Marilandia do Sul
41	Parana	4115754	Maua da Serra
41	Parana	4117297	Novo Itacolomi
41	Parana	4122701	Sabaudia
41	Parana	4103701	Cambe
41	Parana	4109807	Ibipora
41	Parana	4113700	Londrina
41	Parana	4119657	Pitangueiras
41	Parana	4122404	Rolandia
41	Parana	4126678	Tamarana
41	Parana	4103206	Bom Sucesso
41	Parana	4103305	Borrazopolis
41	Parana	4106852	Cruzmaltina
41	Parana	4107603	Faxinal
41	Parana	4113106	Kalore
41	Parana	4115507	Marumbi
41	Parana	4122107	Rio Bom
41	Parana	4101655	Arapua
41	Parana	4101853	Ariranha do Ivai
41	Parana	4104402	Candido de Abreu
41	Parana	4108551	Godoy Moreira
41	Parana	4108700	Grandes Rios
41	Parana	4111506	Ivaipora
41	Parana	4112504	Jardim Alegre
41	Parana	4113429	Lidianopolis
41	Parana	4113759	Lunardelli
41	Parana	4114500	Manoel Ribas
41	Parana	4117271	Nova Tebas
41	Parana	4122172	Rio Branco do Ivai
41	Parana	4122651	Rosario do Ivai
41	Parana	4125001	Sao Joao do Ivai
41	Parana	4125803	Sao Pedro do Ivai
41	Parana	4101903	Assai
41	Parana	4112702	Jataizinho
41	Parana	4117214	Nova Santa Barbara
41	Parana	4121307	Rancho Alegre
41	Parana	4123204	Santa Cecilia do Pavao
41	Parana	4124707	Sao Jeronimo da Serra
41	Parana	4126009	Sao Sebastiao da Amoreira
41	Parana	4128401	Urai
41	Parana	4100103	Abatia
41	Parana	4101101	Andira
41	Parana	4102406	Bandeirantes
41	Parana	4106001	Congonhinhas
41	Parana	4106407	Cornelio Procopio
41	Parana	4111001	Itambaraca
41	Parana	4113403	Leopolis
41	Parana	4116604	Nova America da Colina
41	Parana	4117008	Nova Fatima
41	Parana	4121901	Ribeirao do Pinhal
41	Parana	4123105	Santa Amelia
41	Parana	4123907	Santa Mariana
41	Parana	4124301	Santo Antonio do Paraiso
41	Parana	4126405	Sertaneja
41	Parana	4102703	Barra do Jacare
41	Parana	4103602	Cambara
41	Parana	4111803	Jacarezinho
41	Parana	4112900	Jundiai do Sul
41	Parana	4121802	Ribeirao Claro
41	Parana	4124103	Santo Antonio da Platina
41	Parana	4106100	Conselheiro Mairinck
41	Parana	4107009	Curiuva
41	Parana	4107751	Figueira
41	Parana	4109708	Ibaiti
41	Parana	4111704	Jaboti
41	Parana	4112306	Japira
41	Parana	4119202	Pinhalao
41	Parana	4126207	Sapopema
41	Parana	4104709	Carlopolis
41	Parana	4109005	Guapirama
41	Parana	4112801	Joaquim Tavora
41	Parana	4120705	Quatigua
41	Parana	4122909	Salto do Itarare
41	Parana	4124004	Santana do Itarare
41	Parana	4125407	Sao Jose da Boa Vista
41	Parana	4126603	Siqueira Campos
41	Parana	4127809	Tomazina
41	Parana	4128500	Wenceslau Braz
41	Parana	4110078	Imbau
41	Parana	4117305	Ortigueira
41	Parana	4121703	Reserva
41	Parana	4127106	Telemaco Borba
41	Parana	4127502	Tibagi
41	Parana	4128534	Ventania
41	Parana	4101606	Arapoti
41	Parana	4112009	Jaguariaiva
41	Parana	4119400	Pirai do Sul
41	Parana	4126306	Senges
41	Parana	4104659	Carambei
41	Parana	4104907	Castro
41	Parana	4117701	Palmeira
41	Parana	4119905	Ponta Grossa
41	Parana	4102000	Assis Chateaubriand
41	Parana	4107157	Diamante D'Oeste
41	Parana	4107538	Entre Rios do Oeste
41	Parana	4108205	Formosa do Oeste
41	Parana	4108809	Guaira
41	Parana	4110656	Iracema do Oeste
41	Parana	4112751	Jesuitas
41	Parana	4114609	Marechal Candido Rondon
41	Parana	4115358	Maripa
41	Parana	4115853	Mercedes
41	Parana	4117222	Nova Santa Rosa
41	Parana	4117453	Ouro Verde do Oeste
41	Parana	4117909	Palotina
41	Parana	4118451	Pato Bragado
41	Parana	4120853	Quatro Pontes
41	Parana	4123501	Santa Helena
41	Parana	4125456	Sao Jose das Palmeiras
41	Parana	4125753	Sao Pedro do Iguacu
41	Parana	4127403	Terra Roxa
41	Parana	4127700	Toledo
41	Parana	4127957	Tupassi
41	Parana	4101051	Anahy
41	Parana	4103057	Boa Vista da Aparecida
41	Parana	4103354	Braganey
41	Parana	4103453	Cafelandia
41	Parana	4104055	Campo Bonito
41	Parana	4104600	Capitao Leonidas Marques
41	Parana	4104808	Cascavel
41	Parana	4105003	Catanduvas
41	Parana	4106308	Corbelia
41	Parana	4107124	Diamante do Sul
41	Parana	4109302	Guaraniacu
41	Parana	4109757	Ibema
41	Parana	4110052	Iguatu
41	Parana	4113452	Lindoeste
41	Parana	4116703	Nova Aurora
41	Parana	4123824	Santa Lucia
41	Parana	4124020	Santa Tereza do Oeste
41	Parana	4127858	Tres Barras do Parana
41	Parana	4105300	Ceu Azul
41	Parana	4108304	Foz do Iguacu
41	Parana	4110953	Itaipulandia
41	Parana	4115606	Matelandia
41	Parana	4115804	Medianeira
41	Parana	4116059	Missal
41	Parana	4121257	Ramilandia
41	Parana	4124053	Santa Terezinha de Itaipu
41	Parana	4125704	Sao Miguel do Iguacu
41	Parana	4126355	Serranopolis do Iguacu
41	Parana	4128559	Vera Cruz do Oeste
41	Parana	4101002	Ampere
41	Parana	4102752	Bela Vista da Caroba
41	Parana	4104501	Capanema
41	Parana	4119004	Perola d'Oeste
41	Parana	4119806	Planalto
41	Parana	4120358	Pranchita
41	Parana	4121406	Realeza
41	Parana	4123808	Santa Izabel do Oeste
41	Parana	4102604	Barracao
41	Parana	4103024	Boa Esperanca do Iguacu
41	Parana	4103156	Bom Jesus do Sul
41	Parana	4106571	Cruzeiro do Iguacu
41	Parana	4107207	Dois Vizinhos
41	Parana	4107405	Eneas Marques
41	Parana	4107850	Flor da Serra do Sul
41	Parana	4108403	Francisco Beltrao
41	Parana	4114351	Manfrinopolis
41	Parana	4115408	Marmeleiro
41	Parana	4116950	Nova Esperanca do Sudoeste
41	Parana	4117255	Nova Prata do Iguacu
41	Parana	4119251	Pinhal de Sao Bento
41	Parana	4121604	Renascenca
41	Parana	4122800	Salgado Filho
41	Parana	4123006	Salto do Lontra
41	Parana	4124400	Santo Antonio do Sudoeste
41	Parana	4125209	Sao Jorge d'Oeste
41	Parana	4128609	Vere
41	Parana	4103222	Bom Sucesso do Sul
41	Parana	4105409	Chopinzinho
41	Parana	4106506	Coronel Vivida
41	Parana	4111209	Itapejara d'Oeste
41	Parana	4115309	Mariopolis
41	Parana	4118501	Pato Branco
41	Parana	4124806	Sao Joao
41	Parana	4126272	Saudade do Iguacu
41	Parana	4126652	Sulina
41	Parana	4128708	Vitorino
41	Parana	4103040	Boa Ventura de Sao Roque
41	Parana	4113254	Laranjal
41	Parana	4115739	Mato Rico
41	Parana	4117800	Palmital
41	Parana	4119608	Pitanga
41	Parana	4123857	Santa Maria do Oeste
41	Parana	4103958	Campina do Simao
41	Parana	4104428	Candoi
41	Parana	4104451	Cantagalo
41	Parana	4107546	Espigao Alto do Iguacu
41	Parana	4108452	Foz do Jordao
41	Parana	4108650	Goioxim
41	Parana	4109401	Guarapuava
41	Parana	4110201	Inacio Martins
41	Parana	4113304	Laranjeiras do Sul
41	Parana	4115457	Marquinho
41	Parana	4117057	Nova Laranjeiras
41	Parana	4119301	Pinhao
41	Parana	4120150	Porto Barreiro
41	Parana	4120903	Quedas do Iguacu
41	Parana	4121752	Reserva do Iguacu
41	Parana	4122156	Rio Bonito do Iguacu
41	Parana	4127965	Turvo
41	Parana	4128658	Virmond
41	Parana	4105706	Clevelandia
41	Parana	4106456	Coronel Domingos Soares
41	Parana	4109658	Honorio Serpa
41	Parana	4114401	Mangueirinha
41	Parana	4117602	Palmas
41	Parana	4107736	Fernandes Pinheiro
41	Parana	4108957	Guamiranga
41	Parana	4110102	Imbituva
41	Parana	4110508	Ipiranga
41	Parana	4111407	Ivai
41	Parana	4120606	Prudentopolis
41	Parana	4127007	Teixeira Soares
41	Parana	4110706	Irati
41	Parana	4113908	Mallet
41	Parana	4121505	Reboucas
41	Parana	4122008	Rio Azul
41	Parana	4102901	Bituruna
41	Parana	4106803	Cruz Machado
41	Parana	4108502	General Carneiro
41	Parana	4118600	Paula Freitas
41	Parana	4118709	Paulo Frontin
41	Parana	4120309	Porto Vitoria
41	Parana	4128203	Uniao da Vitoria
41	Parana	4101309	Antonio Olinto
41	Parana	4125100	Sao Joao do Triunfo
41	Parana	4125605	Sao Mateus do Sul
41	Parana	4100202	Adrianopolis
41	Parana	4105201	Cerro Azul
41	Parana	4128633	Doutor Ulysses
41	Parana	4113205	Lapa
41	Parana	4120101	Porto Amazonas
41	Parana	4100400	Almirante Tamandare
41	Parana	4101804	Araucaria
41	Parana	4102307	Balsa Nova
41	Parana	4103107	Bocaiuva do Sul
41	Parana	4104006	Campina Grande do Sul
41	Parana	4104204	Campo Largo
41	Parana	4104253	Campo Magro
41	Parana	4105805	Colombo
41	Parana	4106209	Contenda
41	Parana	4106902	Curitiba
41	Parana	4107652	Fazenda Rio Grande
41	Parana	4111258	Itaperucu
41	Parana	4114302	Mandirituba
41	Parana	4119152	Pinhais
41	Parana	4119509	Piraquara
41	Parana	4120804	Quatro Barras
41	Parana	4122206	Rio Branco do Sul
41	Parana	4125506	Sao Jose dos Pinhais
41	Parana	4127882	Tunas do Parana
41	Parana	4101200	Antonina
41	Parana	4109500	Guaraquecaba
41	Parana	4109609	Guaratuba
41	Parana	4115705	Matinhos
41	Parana	4116208	Morretes
41	Parana	4118204	Paranagua
41	Parana	4119954	Pontal do Parana
41	Parana	4100301	Agudos do Sul
41	Parana	4104105	Campo do Tenente
41	Parana	4119103	Pien
41	Parana	4121208	Quitandinha
41	Parana	4122305	Rio Negro
41	Parana	4127601	Tijucas do Sul
42	Santa Catarina	4200804	Anchieta
42	Santa Catarina	4202081	Bandeirante
42	Santa Catarina	4202099	Barra Bonita
42	Santa Catarina	4202156	Belmonte
42	Santa Catarina	4204905	Descanso
42	Santa Catarina	4205001	Dionisio Cerqueira
42	Santa Catarina	4206405	Guaraciaba
42	Santa Catarina	4206603	Guaruja do Sul
42	Santa Catarina	4207650	Ipora do Oeste
42	Santa Catarina	4208401	Itapiranga
42	Santa Catarina	4211009	Mondai
42	Santa Catarina	4212007	Palma Sola
42	Santa Catarina	4212239	Paraiso
42	Santa Catarina	4214151	Princesa
42	Santa Catarina	4215075	Riqueza
42	Santa Catarina	4215208	Romelandia
42	Santa Catarina	4215554	Santa Helena
42	Santa Catarina	4216255	Sao Joao do Oeste
42	Santa Catarina	4216701	Sao Jose do Cedro
42	Santa Catarina	4217204	Sao Miguel do Oeste
42	Santa Catarina	4218756	Tunapolis
42	Santa Catarina	4200507	aguas de Chapeco
42	Santa Catarina	4200556	aguas Frias
42	Santa Catarina	4202578	Bom Jesus do Oeste
42	Santa Catarina	4203105	Caibi
42	Santa Catarina	4203501	Campo Ere
42	Santa Catarina	4204103	Caxambu do Sul
42	Santa Catarina	4204202	Chapeco
42	Santa Catarina	4204350	Cordilheira Alta
42	Santa Catarina	4204400	Coronel Freitas
42	Santa Catarina	4204707	Cunha Pora
42	Santa Catarina	4204756	Cunhatai
42	Santa Catarina	4205357	Flor do Sertao
42	Santa Catarina	4205431	Formosa do Sul
42	Santa Catarina	4206652	Guatambu
42	Santa Catarina	4207759	Iraceminha
42	Santa Catarina	4207858	Irati
42	Santa Catarina	4208955	Jardinopolis
42	Santa Catarina	4210506	Maravilha
42	Santa Catarina	4210902	Modelo
42	Santa Catarina	4211405	Nova Erechim
42	Santa Catarina	4211454	Nova Itaberaba
42	Santa Catarina	4211652	Novo Horizonte
42	Santa Catarina	4212106	Palmitos
42	Santa Catarina	4212908	Pinhalzinho
42	Santa Catarina	4213153	Planalto Alegre
42	Santa Catarina	4214201	Quilombo
42	Santa Catarina	4215356	Saltinho
42	Santa Catarina	4215687	Santa Terezinha do Progresso
42	Santa Catarina	4215695	Santiago do Sul
42	Santa Catarina	4215752	Sao Bernardino
42	Santa Catarina	4216008	Sao Carlos
42	Santa Catarina	4216909	Sao Lourenco do Oeste
42	Santa Catarina	4217154	Sao Miguel da Boa Vista
42	Santa Catarina	4217303	Saudades
42	Santa Catarina	4217550	Serra Alta
42	Santa Catarina	4217758	Sul Brasil
42	Santa Catarina	4217956	Tigrinhos
42	Santa Catarina	4218855	Uniao do Oeste
42	Santa Catarina	4200101	Abelardo Luz
42	Santa Catarina	4202537	Bom Jesus
42	Santa Catarina	4204459	Coronel Martins
42	Santa Catarina	4205175	Entre Rios
42	Santa Catarina	4205308	Faxinal dos Guedes
42	Santa Catarina	4205605	Galvao
42	Santa Catarina	4207684	Ipuacu
42	Santa Catarina	4209177	Jupia
42	Santa Catarina	4209458	Lajeado Grande
42	Santa Catarina	4210555	Marema
42	Santa Catarina	4211850	Ouro Verde
42	Santa Catarina	4212270	Passos Maia
42	Santa Catarina	4213401	Ponte Serrada
42	Santa Catarina	4216107	Sao Domingos
42	Santa Catarina	4219101	Vargeao
42	Santa Catarina	4219507	Xanxere
42	Santa Catarina	4219705	Xaxim
42	Santa Catarina	4200408	agua Doce
42	Santa Catarina	4201604	Arroio Trinta
42	Santa Catarina	4203006	Cacador
42	Santa Catarina	4203154	Calmon
42	Santa Catarina	4203907	Capinzal
42	Santa Catarina	4204004	Catanduvas
42	Santa Catarina	4205209	Erval Velho
42	Santa Catarina	4205506	Fraiburgo
42	Santa Catarina	4206702	Herval d'Oeste
42	Santa Catarina	4206751	Ibiam
42	Santa Catarina	4206801	Ibicare
42	Santa Catarina	4207577	Iomere
42	Santa Catarina	4208609	Jabora
42	Santa Catarina	4209003	Joacaba
42	Santa Catarina	4209201	Lacerdopolis
42	Santa Catarina	4209706	Lebon Regis
42	Santa Catarina	4210035	Luzerna
42	Santa Catarina	4210050	Macieira
42	Santa Catarina	4210704	Matos Costa
42	Santa Catarina	4211801	Ouro
42	Santa Catarina	4213005	Pinheiro Preto
42	Santa Catarina	4214409	Rio das Antas
42	Santa Catarina	4215406	Salto Veloso
42	Santa Catarina	4217907	Tangara
42	Santa Catarina	4218509	Treze Tilias
42	Santa Catarina	4219176	Vargem Bonita
42	Santa Catarina	4219309	Videira
42	Santa Catarina	4200754	Alto Bela Vista
42	Santa Catarina	4201273	Arabuta
42	Santa Catarina	4201653	Arvoredo
42	Santa Catarina	4204301	Concordia
42	Santa Catarina	4207601	Ipira
42	Santa Catarina	4207700	Ipumirim
42	Santa Catarina	4207809	Irani
42	Santa Catarina	4208005	Ita
42	Santa Catarina	4209854	Lindoia do Sul
42	Santa Catarina	4211876	Paial
42	Santa Catarina	4212601	Peritiba
42	Santa Catarina	4213104	Piratuba
42	Santa Catarina	4213906	Presidente Castello Branco
42	Santa Catarina	4217501	Seara
42	Santa Catarina	4219606	Xavantina
42	Santa Catarina	4202131	Bela Vista do Toldo
42	Santa Catarina	4203808	Canoinhas
42	Santa Catarina	4207908	Irineopolis
42	Santa Catarina	4208104	Itaiopolis
42	Santa Catarina	4210100	Mafra
42	Santa Catarina	4210308	Major Vieira
42	Santa Catarina	4211108	Monte Castelo
42	Santa Catarina	4212205	Papanduva
42	Santa Catarina	4213609	Porto Uniao
42	Santa Catarina	4215679	Santa Terezinha
42	Santa Catarina	4218251	Timbo Grande
42	Santa Catarina	4218301	Tres Barras
42	Santa Catarina	4203303	Campo Alegre
42	Santa Catarina	4215000	Rio Negrinho
42	Santa Catarina	4215802	Sao Bento do Sul
42	Santa Catarina	4201307	Araquari
42	Santa Catarina	4202057	Balneario Barra do Sul
42	Santa Catarina	4204509	Corupa
42	Santa Catarina	4205803	Garuva
42	Santa Catarina	4206504	Guaramirim
42	Santa Catarina	4208450	Itapoa
42	Santa Catarina	4208906	Jaragua do Sul
42	Santa Catarina	4209102	Joinville
42	Santa Catarina	4210605	Massaranduba
42	Santa Catarina	4216206	Sao Francisco do Sul
42	Santa Catarina	4217402	Schroeder
42	Santa Catarina	4200051	Abdon Batista
42	Santa Catarina	4202875	Brunopolis
42	Santa Catarina	4203600	Campos Novos
42	Santa Catarina	4204806	Curitibanos
42	Santa Catarina	4205555	Frei Rogerio
42	Santa Catarina	4211058	Monte Carlo
42	Santa Catarina	4213302	Ponte Alta
42	Santa Catarina	4213351	Ponte Alta do Norte
42	Santa Catarina	4215505	Santa Cecilia
42	Santa Catarina	4216057	Sao Cristovao do Sul
42	Santa Catarina	4219150	Vargem
42	Santa Catarina	4219853	Zortea
42	Santa Catarina	4201000	Anita Garibaldi
42	Santa Catarina	4202438	Bocaina do Sul
42	Santa Catarina	4202503	Bom Jardim da Serra
42	Santa Catarina	4202602	Bom Retiro
42	Santa Catarina	4203253	Capao Alto
42	Santa Catarina	4203402	Campo Belo do Sul
42	Santa Catarina	4204152	Celso Ramos
42	Santa Catarina	4204178	Cerro Negro
42	Santa Catarina	4204558	Correia Pinto
42	Santa Catarina	4209300	Lages
42	Santa Catarina	4211751	Otacilio Costa
42	Santa Catarina	4211892	Painel
42	Santa Catarina	4212056	Palmeira
42	Santa Catarina	4215059	Rio Rufino
42	Santa Catarina	4216503	Sao Joaquim
42	Santa Catarina	4216800	Sao Jose do Cerrito
42	Santa Catarina	4218905	Urubici
42	Santa Catarina	4218954	Urupema
42	Santa Catarina	4200309	Agronomica
42	Santa Catarina	4201901	Aurora
42	Santa Catarina	4202859	Braco do Trombudo
42	Santa Catarina	4205100	Dona Emma
42	Santa Catarina	4206900	Ibirama
42	Santa Catarina	4209151	Jose Boiteux
42	Santa Catarina	4209508	Laurentino
42	Santa Catarina	4209904	Lontras
42	Santa Catarina	4210852	Mirim Doce
42	Santa Catarina	4213708	Pouso Redondo
42	Santa Catarina	4214003	Presidente Getulio
42	Santa Catarina	4214102	Presidente Nereu
42	Santa Catarina	4214508	Rio do Campo
42	Santa Catarina	4214607	Rio do Oeste
42	Santa Catarina	4214805	Rio do Sul
42	Santa Catarina	4215307	Salete
42	Santa Catarina	4217808	Taio
42	Santa Catarina	4218608	Trombudo Central
42	Santa Catarina	4219358	Vitor Meireles
42	Santa Catarina	4219408	Witmarsum
42	Santa Catarina	4201257	Apiuna
42	Santa Catarina	4201703	Ascurra
42	Santa Catarina	4202206	Benedito Novo
42	Santa Catarina	4202404	Blumenau
42	Santa Catarina	4202701	Botuvera
42	Santa Catarina	4202909	Brusque
42	Santa Catarina	4205159	Doutor Pedrinho
42	Santa Catarina	4205902	Gaspar
42	Santa Catarina	4206306	Guabiruba
42	Santa Catarina	4207502	Indaial
42	Santa Catarina	4210001	Luiz Alves
42	Santa Catarina	4213203	Pomerode
42	Santa Catarina	4214706	Rio dos Cedros
42	Santa Catarina	4215109	Rodeio
42	Santa Catarina	4218202	Timbo
42	Santa Catarina	4202008	Balneario Camboriu
42	Santa Catarina	4202107	Barra Velha
42	Santa Catarina	4202453	Bombinhas
42	Santa Catarina	4203204	Camboriu
42	Santa Catarina	4207106	Ilhota
42	Santa Catarina	4208203	Itajai
42	Santa Catarina	4208302	Itapema
42	Santa Catarina	4211306	Navegantes
42	Santa Catarina	4212502	Penha
42	Santa Catarina	4212809	Balneario Picarras
42	Santa Catarina	4213500	Porto Belo
42	Santa Catarina	4216354	Sao Joao do Itaperiu
42	Santa Catarina	4200200	Agrolandia
42	Santa Catarina	4201802	Atalanta
42	Santa Catarina	4204194	Chapadao do Lageado
42	Santa Catarina	4207403	Imbuia
42	Santa Catarina	4208500	Ituporanga
42	Santa Catarina	4212700	Petrolandia
42	Santa Catarina	4219200	Vidal Ramos
42	Santa Catarina	4200903	Angelina
42	Santa Catarina	4203709	Canelinha
42	Santa Catarina	4209805	Leoberto Leal
42	Santa Catarina	4210209	Major Gercino
42	Santa Catarina	4211504	Nova Trento
42	Santa Catarina	4216305	Sao Joao Batista
42	Santa Catarina	4218004	Tijucas
42	Santa Catarina	4201208	Antonio Carlos
42	Santa Catarina	4202305	Biguacu
42	Santa Catarina	4205407	Florianopolis
42	Santa Catarina	4206009	Governador Celso Ramos
42	Santa Catarina	4211900	Palhoca
42	Santa Catarina	4212304	Paulo Lopes
42	Santa Catarina	4215703	Santo Amaro da Imperatriz
42	Santa Catarina	4216602	Sao Jose
42	Santa Catarina	4217253	Sao Pedro de Alcantara
42	Santa Catarina	4200606	aguas Mornas
42	Santa Catarina	4200705	Alfredo Wagner
42	Santa Catarina	4201109	Anitapolis
42	Santa Catarina	4214300	Rancho Queimado
42	Santa Catarina	4215901	Sao Bonifacio
42	Santa Catarina	4201505	Armazem
42	Santa Catarina	4202800	Braco do Norte
42	Santa Catarina	4203956	Capivari de Baixo
42	Santa Catarina	4205704	Garopaba
42	Santa Catarina	4206108	Grao Para
42	Santa Catarina	4206207	Gravatal
42	Santa Catarina	4207205	Imarui
42	Santa Catarina	4207304	Imbituba
42	Santa Catarina	4208807	Jaguaruna
42	Santa Catarina	4209409	Laguna
42	Santa Catarina	4211702	Orleans
42	Santa Catarina	4212403	Pedras Grandes
42	Santa Catarina	4214904	Rio Fortuna
42	Santa Catarina	4215455	Sangao
42	Santa Catarina	4215604	Santa Rosa de Lima
42	Santa Catarina	4217006	Sao Ludgero
42	Santa Catarina	4217105	Sao Martinho
42	Santa Catarina	4218400	Treze de Maio
42	Santa Catarina	4218707	Tubarao
42	Santa Catarina	4204251	Cocal do Sul
42	Santa Catarina	4204608	Criciuma
42	Santa Catarina	4205456	Forquilhinha
42	Santa Catarina	4207007	Icara
42	Santa Catarina	4209607	Lauro Muller
42	Santa Catarina	4211207	Morro da Fumaca
42	Santa Catarina	4211603	Nova Veneza
42	Santa Catarina	4217600	Sideropolis
42	Santa Catarina	4218350	Treviso
42	Santa Catarina	4219002	Urussanga
42	Santa Catarina	4201406	Ararangua
42	Santa Catarina	4201950	Balneario Arroio do Silva
42	Santa Catarina	4202073	Balneario Gaivota
42	Santa Catarina	4205191	Ermo
42	Santa Catarina	4208708	Jacinto Machado
42	Santa Catarina	4210407	Maracaja
42	Santa Catarina	4210803	Meleiro
42	Santa Catarina	4211256	Morro Grande
42	Santa Catarina	4212254	Passo de Torres
42	Santa Catarina	4213807	Praia Grande
42	Santa Catarina	4215653	Santa Rosa do Sul
42	Santa Catarina	4216404	Sao Joao do Sul
42	Santa Catarina	4217709	Sombrio
42	Santa Catarina	4218103	Timbe do Sul
42	Santa Catarina	4218806	Turvo
43	Rio Grande do Sul	4300307	Alecrim
43	Rio Grande do Sul	4304309	Candido Godoi
43	Rio Grande do Sul	4310405	Independencia
43	Rio Grande do Sul	4313425	Novo Machado
43	Rio Grande do Sul	4315008	Porto Lucena
43	Rio Grande do Sul	4315057	Porto Maua
43	Rio Grande do Sul	4315073	Porto Vera Cruz
43	Rio Grande do Sul	4317202	Santa Rosa
43	Rio Grande do Sul	4317905	Santo Cristo
43	Rio Grande do Sul	4318499	Sao Jose do Inhacora
43	Rio Grande do Sul	4321808	Tres de Maio
43	Rio Grande do Sul	4322103	Tucunduva
43	Rio Grande do Sul	4322301	Tuparendi
43	Rio Grande do Sul	4301859	Barra do Guarita
43	Rio Grande do Sul	4302204	Boa Vista do Burica
43	Rio Grande do Sul	4302378	Bom Progresso
43	Rio Grande do Sul	4302600	Braga
43	Rio Grande do Sul	4304002	Campo Novo
43	Rio Grande do Sul	4306007	Crissiumal
43	Rio Grande do Sul	4306320	Derrubadas
43	Rio Grande do Sul	4306734	Doutor Mauricio Cardoso
43	Rio Grande do Sul	4307450	Esperanca do Sul
43	Rio Grande do Sul	4309605	Horizontina
43	Rio Grande do Sul	4309704	Humaita
43	Rio Grande do Sul	4312302	Miraguai
43	Rio Grande do Sul	4313011	Nova Candelaria
43	Rio Grande do Sul	4315404	Redentora
43	Rio Grande do Sul	4319109	Sao Martinho
43	Rio Grande do Sul	4320230	Sede Nova
43	Rio Grande do Sul	4321402	Tenente Portela
43	Rio Grande do Sul	4321477	Tiradentes do Sul
43	Rio Grande do Sul	4321907	Tres Passos
43	Rio Grande do Sul	4323705	Vista Gaucha
43	Rio Grande do Sul	4300505	Alpestre
43	Rio Grande do Sul	4300646	Ametista do Sul
43	Rio Grande do Sul	4303400	Caicara
43	Rio Grande do Sul	4305801	Constantina
43	Rio Grande do Sul	4306072	Cristal do Sul
43	Rio Grande do Sul	4306429	Dois Irmaos das Missoes
43	Rio Grande do Sul	4306924	Engenho Velho
43	Rio Grande do Sul	4307302	Erval Seco
43	Rio Grande do Sul	4308508	Frederico Westphalen
43	Rio Grande do Sul	4309126	Gramado dos Loureiros
43	Rio Grande do Sul	4310504	Irai
43	Rio Grande do Sul	4311601	Liberato Salzano
43	Rio Grande do Sul	4312708	Nonoai
43	Rio Grande do Sul	4313441	Novo Tiradentes
43	Rio Grande do Sul	4313466	Novo Xingu
43	Rio Grande do Sul	4313805	Palmitinho
43	Rio Grande do Sul	4314498	Pinheirinho do Vale
43	Rio Grande do Sul	4314704	Planalto
43	Rio Grande do Sul	4315552	Rio dos indios
43	Rio Grande do Sul	4315909	Rodeio Bonito
43	Rio Grande do Sul	4316204	Rondinha
43	Rio Grande do Sul	4320206	Seberi
43	Rio Grande do Sul	4321329	Taquarucu do Sul
43	Rio Grande do Sul	4321857	Tres Palmeiras
43	Rio Grande do Sul	4321956	Trindade do Sul
43	Rio Grande do Sul	4323101	Vicente Dutra
43	Rio Grande do Sul	4323507	Vista Alegre
43	Rio Grande do Sul	4300901	Aratiba
43	Rio Grande do Sul	4301552	aurea
43	Rio Grande do Sul	4301701	Barao de Cotegipe
43	Rio Grande do Sul	4301925	Barra do Rio Azul
43	Rio Grande do Sul	4302055	Benjamin Constant do Sul
43	Rio Grande do Sul	4303806	Campinas do Sul
43	Rio Grande do Sul	4304853	Carlos Gomes
43	Rio Grande do Sul	4305116	Centenario
43	Rio Grande do Sul	4306130	Cruzaltense
43	Rio Grande do Sul	4306957	Entre Rios do Sul
43	Rio Grande do Sul	4306973	Erebango
43	Rio Grande do Sul	4307005	Erechim
43	Rio Grande do Sul	4307203	Erval Grande
43	Rio Grande do Sul	4307559	Estacao
43	Rio Grande do Sul	4308052	Faxinalzinho
43	Rio Grande do Sul	4308250	Floriano Peixoto
43	Rio Grande do Sul	4308706	Gaurama
43	Rio Grande do Sul	4308904	Getulio Vargas
43	Rio Grande do Sul	4310462	Ipiranga do Sul
43	Rio Grande do Sul	4310702	Itatiba do Sul
43	Rio Grande do Sul	4310900	Jacutinga
43	Rio Grande do Sul	4311908	Marcelino Ramos
43	Rio Grande do Sul	4312005	Mariano Moro
43	Rio Grande do Sul	4314134	Paulo Bento
43	Rio Grande do Sul	4314787	Ponte Preta
43	Rio Grande do Sul	4315313	Quatro Irmaos
43	Rio Grande do Sul	4319703	Sao Valentim
43	Rio Grande do Sul	4320602	Severiano de Almeida
43	Rio Grande do Sul	4321634	Tres Arroios
43	Rio Grande do Sul	4322905	Viadutos
43	Rio Grande do Sul	4301800	Barracao
43	Rio Grande do Sul	4303202	Cacique Doble
43	Rio Grande do Sul	4309803	Ibiaca
43	Rio Grande do Sul	4311700	Machadinho
43	Rio Grande do Sul	4312203	Maximiliano de Almeida
43	Rio Grande do Sul	4313607	Paim Filho
43	Rio Grande do Sul	4316600	Sananduva
43	Rio Grande do Sul	4317954	Santo Expedito do Sul
43	Rio Grande do Sul	4318424	Sao Joao da Urtiga
43	Rio Grande do Sul	4318606	Sao Jose do Ouro
43	Rio Grande do Sul	4322186	Tupanci do Sul
43	Rio Grande do Sul	4303301	Caibate
43	Rio Grande do Sul	4303707	Campina das Missoes
43	Rio Grande do Sul	4305207	Cerro Largo
43	Rio Grande do Sul	4309506	Guarani das Missoes
43	Rio Grande do Sul	4312179	Mato Queimado
43	Rio Grande do Sul	4315107	Porto Xavier
43	Rio Grande do Sul	4316303	Roque Gonzales
43	Rio Grande do Sul	4316477	Salvador das Missoes
43	Rio Grande do Sul	4319307	Sao Paulo das Missoes
43	Rio Grande do Sul	4319372	Sao Pedro do Butia
43	Rio Grande do Sul	4320578	Sete de Setembro
43	Rio Grande do Sul	4302501	Bossoroca
43	Rio Grande do Sul	4305009	Catuipe
43	Rio Grande do Sul	4306353	Dezesseis de Novembro
43	Rio Grande do Sul	4306932	Entre-Ijuis
43	Rio Grande do Sul	4307831	Eugenio de Castro
43	Rio Grande do Sul	4309001	Girua
43	Rio Grande do Sul	4314555	Pirapo
43	Rio Grande do Sul	4315958	Rolador
43	Rio Grande do Sul	4317509	Santo angelo
43	Rio Grande do Sul	4317707	Santo Antonio das Missoes
43	Rio Grande do Sul	4318903	Sao Luiz Gonzaga
43	Rio Grande do Sul	4319158	Sao Miguel das Missoes
43	Rio Grande do Sul	4319208	Sao Nicolau
43	Rio Grande do Sul	4320321	Senador Salgado Filho
43	Rio Grande do Sul	4322343	Ubiretama
43	Rio Grande do Sul	4323754	Vitoria das Missoes
43	Rio Grande do Sul	4300208	Ajuricaba
43	Rio Grande do Sul	4300455	Alegria
43	Rio Grande do Sul	4301503	Augusto Pestana
43	Rio Grande do Sul	4302584	Bozano
43	Rio Grande do Sul	4305405	Chiapetta
43	Rio Grande do Sul	4305702	Condor
43	Rio Grande do Sul	4305871	Coronel Barros
43	Rio Grande do Sul	4305900	Coronel Bicaco
43	Rio Grande do Sul	4310207	Ijui
43	Rio Grande do Sul	4310413	Inhacora
43	Rio Grande do Sul	4313334	Nova Ramada
43	Rio Grande do Sul	4313904	Panambi
43	Rio Grande do Sul	4314308	Pejucara
43	Rio Grande do Sul	4317806	Santo Augusto
43	Rio Grande do Sul	4319737	Sao Valerio do Sul
43	Rio Grande do Sul	4300471	Almirante Tamandare do Sul
43	Rio Grande do Sul	4301958	Barra Funda
43	Rio Grande do Sul	4302154	Boa Vista das Missoes
43	Rio Grande do Sul	4304705	Carazinho
43	Rio Grande do Sul	4305157	Cerro Grande
43	Rio Grande do Sul	4305306	Chapada
43	Rio Grande do Sul	4305850	Coqueiros do Sul
43	Rio Grande do Sul	4310850	Jaboticaba
43	Rio Grande do Sul	4311429	Lajeado do Bugre
43	Rio Grande do Sul	4312955	Nova Boa Vista
43	Rio Grande do Sul	4313490	Novo Barreiro
43	Rio Grande do Sul	4313706	Palmeira das Missoes
43	Rio Grande do Sul	4314456	Pinhal
43	Rio Grande do Sul	4316428	Sagrada Familia
43	Rio Grande do Sul	4317756	Santo Antonio do Planalto
43	Rio Grande do Sul	4318457	Sao Jose das Missoes
43	Rio Grande do Sul	4319364	Sao Pedro das Missoes
43	Rio Grande do Sul	4320107	Sarandi
43	Rio Grande do Sul	4300059	agua Santa
43	Rio Grande do Sul	4303558	Camargo
43	Rio Grande do Sul	4304903	Casca
43	Rio Grande do Sul	4304952	Caseiros
43	Rio Grande do Sul	4305371	Charrua
43	Rio Grande do Sul	4305504	Ciriaco
43	Rio Grande do Sul	4305975	Coxilha
43	Rio Grande do Sul	4306304	David Canabarro
43	Rio Grande do Sul	4307054	Ernestina
43	Rio Grande do Sul	4308854	Gentil
43	Rio Grande do Sul	4309902	Ibiraiaras
43	Rio Grande do Sul	4311809	Marau
43	Rio Grande do Sul	4312138	Mato Castelhano
43	Rio Grande do Sul	4312625	Muliterno
43	Rio Grande do Sul	4312674	Nicolau Vergueiro
43	Rio Grande do Sul	4314100	Passo Fundo
43	Rio Grande do Sul	4314779	Pontao
43	Rio Grande do Sul	4316105	Ronda Alta
43	Rio Grande do Sul	4316733	Santa Cecilia do Sul
43	Rio Grande do Sul	4317558	Santo Antonio do Palma
43	Rio Grande do Sul	4318051	Sao Domingos do Sul
43	Rio Grande do Sul	4320503	Sertao
43	Rio Grande do Sul	4320909	Tapejara
43	Rio Grande do Sul	4322558	Vanini
43	Rio Grande do Sul	4323358	Vila Langaro
43	Rio Grande do Sul	4323408	Vila Maria
43	Rio Grande do Sul	4300554	Alto Alegre
43	Rio Grande do Sul	4302220	Boa Vista do Cadeado
43	Rio Grande do Sul	4302238	Boa Vista do Incra
43	Rio Grande do Sul	4304101	Campos Borges
43	Rio Grande do Sul	4306106	Cruz Alta
43	Rio Grande do Sul	4307500	Espumoso
43	Rio Grande do Sul	4308458	Fortaleza dos Valos
43	Rio Grande do Sul	4310009	Ibiruba
43	Rio Grande do Sul	4310876	Jacuizinho
43	Rio Grande do Sul	4311155	Joia
43	Rio Grande do Sul	4315354	Quinze de Novembro
43	Rio Grande do Sul	4316436	Saldanha Marinho
43	Rio Grande do Sul	4316451	Salto do Jacui
43	Rio Grande do Sul	4316709	Santa Barbara do Sul
43	Rio Grande do Sul	4305603	Colorado
43	Rio Grande do Sul	4311270	Lagoa dos Tres Cantos
43	Rio Grande do Sul	4312658	Nao-Me-Toque
43	Rio Grande do Sul	4320305	Selbach
43	Rio Grande do Sul	4321006	Tapera
43	Rio Grande do Sul	4321469	Tio Hugo
43	Rio Grande do Sul	4323200	Victor Graeff
43	Rio Grande do Sul	4302006	Barros Cassal
43	Rio Grande do Sul	4308300	Fontoura Xavier
43	Rio Grande do Sul	4309951	Ibirapuita
43	Rio Grande do Sul	4311254	Lagoao
43	Rio Grande do Sul	4312427	Mormaco
43	Rio Grande do Sul	4318465	Sao Jose do Herval
43	Rio Grande do Sul	4320800	Soledade
43	Rio Grande do Sul	4322152	Tunas
43	Rio Grande do Sul	4300661	Andre da Rocha
43	Rio Grande do Sul	4300703	Anta Gorda
43	Rio Grande do Sul	4301404	Arvorezinha
43	Rio Grande do Sul	4306452	Dois Lajeados
43	Rio Grande do Sul	4309258	Guabiju
43	Rio Grande do Sul	4309407	Guapore
43	Rio Grande do Sul	4310306	Ilopolis
43	Rio Grande do Sul	4310579	Itapuca
43	Rio Grande do Sul	4312351	Montauri
43	Rio Grande do Sul	4312757	Nova Alvorada
43	Rio Grande do Sul	4312807	Nova Araca
43	Rio Grande do Sul	4312906	Nova Bassano
43	Rio Grande do Sul	4313300	Nova Prata
43	Rio Grande do Sul	4314001	Parai
43	Rio Grande do Sul	4315172	Protasio Alves
43	Rio Grande do Sul	4315206	Putinga
43	Rio Grande do Sul	4318440	Sao Jorge
43	Rio Grande do Sul	4319711	Sao Valentim do Sul
43	Rio Grande do Sul	4320404	Serafina Correa
43	Rio Grande do Sul	4322350	Uniao da Serra
43	Rio Grande do Sul	4323606	Vista Alegre do Prata
43	Rio Grande do Sul	4302303	Bom Jesus
43	Rio Grande do Sul	4303608	Cambara do Sul
43	Rio Grande do Sul	4303673	Campestre da Serra
43	Rio Grande do Sul	4304622	Capao Bonito do Sul
43	Rio Grande do Sul	4307401	Esmeralda
43	Rio Grande do Sul	4310439	Ipe
43	Rio Grande do Sul	4311122	Jaquirana
43	Rio Grande do Sul	4311304	Lagoa Vermelha
43	Rio Grande do Sul	4312377	Monte Alegre dos Campos
43	Rio Grande do Sul	4312617	Muitos Capoes
43	Rio Grande do Sul	4314464	Pinhal da Serra
43	Rio Grande do Sul	4318200	Sao Francisco de Paula
43	Rio Grande do Sul	4318622	Sao Jose dos Ausentes
43	Rio Grande do Sul	4322509	Vacaria
43	Rio Grande do Sul	4300802	Antonio Prado
43	Rio Grande do Sul	4302105	Bento Goncalves
43	Rio Grande do Sul	4302253	Boa Vista do Sul
43	Rio Grande do Sul	4304804	Carlos Barbosa
43	Rio Grande do Sul	4305108	Caxias do Sul
43	Rio Grande do Sul	4305934	Coronel Pilar
43	Rio Grande do Sul	4305959	Cotipora
43	Rio Grande do Sul	4307864	Fagundes Varela
43	Rio Grande do Sul	4307906	Farroupilha
43	Rio Grande do Sul	4308201	Flores da Cunha
43	Rio Grande do Sul	4308607	Garibaldi
43	Rio Grande do Sul	4312385	Monte Belo do Sul
43	Rio Grande do Sul	4313086	Nova Padua
43	Rio Grande do Sul	4313359	Nova Roma do Sul
43	Rio Grande do Sul	4317251	Santa Tereza
43	Rio Grande do Sul	4319000	Sao Marcos
43	Rio Grande do Sul	4322806	Veranopolis
43	Rio Grande do Sul	4323309	Vila Flores
43	Rio Grande do Sul	4304655	Capao do Cipo
43	Rio Grande do Sul	4310553	Itacurubi
43	Rio Grande do Sul	4311130	Jari
43	Rio Grande do Sul	4311205	Julio de Castilhos
43	Rio Grande do Sul	4314472	Pinhal Grande
43	Rio Grande do Sul	4315321	Quevedos
43	Rio Grande do Sul	4317400	Santiago
43	Rio Grande do Sul	4322202	Tupancireta
43	Rio Grande do Sul	4322376	Unistalda
43	Rio Grande do Sul	4302907	Cacequi
43	Rio Grande do Sul	4306379	Dilermando de Aguiar
43	Rio Grande do Sul	4310538	Itaara
43	Rio Grande do Sul	4311106	Jaguari
43	Rio Grande do Sul	4312104	Mata
43	Rio Grande do Sul	4313037	Nova Esperanca do Sul
43	Rio Grande do Sul	4316907	Santa Maria
43	Rio Grande do Sul	4319125	Sao Martinho da Serra
43	Rio Grande do Sul	4319406	Sao Pedro do Sul
43	Rio Grande do Sul	4319604	Sao Sepe
43	Rio Grande do Sul	4319802	Sao Vicente do Sul
43	Rio Grande do Sul	4321493	Toropi
43	Rio Grande do Sul	4323457	Vila Nova do Sul
43	Rio Grande do Sul	4300109	Agudo
43	Rio Grande do Sul	4306700	Dona Francisca
43	Rio Grande do Sul	4308003	Faxinal do Soturno
43	Rio Grande do Sul	4308409	Formigueiro
43	Rio Grande do Sul	4310751	Ivora
43	Rio Grande do Sul	4313102	Nova Palma
43	Rio Grande do Sul	4315503	Restinga Seca
43	Rio Grande do Sul	4318432	Sao Joao do Polesine
43	Rio Grande do Sul	4320651	Silveira Martins
43	Rio Grande do Sul	4301206	Arroio do Tigre
43	Rio Grande do Sul	4304200	Candelaria
43	Rio Grande do Sul	4307815	Estrela Velha
43	Rio Grande do Sul	4309159	Gramado Xavier
43	Rio Grande do Sul	4309571	Herveiras
43	Rio Grande do Sul	4309753	Ibarama
43	Rio Grande do Sul	4311239	Lagoa Bonita do Sul
43	Rio Grande do Sul	4312153	Mato Leitao
43	Rio Grande do Sul	4314068	Passa Sete
43	Rio Grande do Sul	4316808	Santa Cruz do Sul
43	Rio Grande do Sul	4320263	Segredo
43	Rio Grande do Sul	4320677	Sinimbu
43	Rio Grande do Sul	4320701	Sobradinho
43	Rio Grande do Sul	4322533	Vale do Sol
43	Rio Grande do Sul	4322608	Venancio Aires
43	Rio Grande do Sul	4322707	Vera Cruz
43	Rio Grande do Sul	4301008	Arroio do Meio
43	Rio Grande do Sul	4302402	Bom Retiro do Sul
43	Rio Grande do Sul	4302451	Boqueirao do Leao
43	Rio Grande do Sul	4304614	Canudos do Vale
43	Rio Grande do Sul	4304697	Capitao
43	Rio Grande do Sul	4305587	Colinas
43	Rio Grande do Sul	4305835	Coqueiro Baixo
43	Rio Grande do Sul	4306205	Cruzeiro do Sul
43	Rio Grande do Sul	4306759	Doutor Ricardo
43	Rio Grande do Sul	4306809	Encantado
43	Rio Grande do Sul	4307807	Estrela
43	Rio Grande do Sul	4308078	Fazenda Vilanova
43	Rio Grande do Sul	4308433	Forquetinha
43	Rio Grande do Sul	4310363	Imigrante
43	Rio Grande do Sul	4311403	Lajeado
43	Rio Grande do Sul	4312054	Marques de Souza
43	Rio Grande do Sul	4312609	Mucum
43	Rio Grande do Sul	4313003	Nova Brescia
43	Rio Grande do Sul	4314159	Paverama
43	Rio Grande do Sul	4315131	Pouso Novo
43	Rio Grande do Sul	4315156	Progresso
43	Rio Grande do Sul	4315453	Relvado
43	Rio Grande do Sul	4315800	Roca Sales
43	Rio Grande do Sul	4316758	Santa Clara do Sul
43	Rio Grande do Sul	4320453	Serio
43	Rio Grande do Sul	4320859	Tabai
43	Rio Grande do Sul	4321303	Taquari
43	Rio Grande do Sul	4321451	Teutonia
43	Rio Grande do Sul	4321626	Travesseiro
43	Rio Grande do Sul	4322855	Vespasiano Correa
43	Rio Grande do Sul	4323770	Westfalia
43	Rio Grande do Sul	4303004	Cachoeira do Sul
43	Rio Grande do Sul	4305132	Cerro Branco
43	Rio Grande do Sul	4313391	Novo Cabrais
43	Rio Grande do Sul	4313953	Pantano Grande
43	Rio Grande do Sul	4314027	Paraiso do Sul
43	Rio Grande do Sul	4314076	Passo do Sobrado
43	Rio Grande do Sul	4315701	Rio Pardo
43	Rio Grande do Sul	4300570	Alto Feliz
43	Rio Grande do Sul	4301651	Barao
43	Rio Grande do Sul	4302352	Bom Principio
43	Rio Grande do Sul	4302659	Brochier
43	Rio Grande do Sul	4304689	Capela de Santana
43	Rio Grande do Sul	4308102	Feliz
43	Rio Grande do Sul	4309555	Harmonia
43	Rio Grande do Sul	4311643	Linha Nova
43	Rio Grande do Sul	4311791	Marata
43	Rio Grande do Sul	4312401	Montenegro
43	Rio Grande do Sul	4314035	Pareci Novo
43	Rio Grande do Sul	4314753	Poco das Antas
43	Rio Grande do Sul	4314803	Portao
43	Rio Grande do Sul	4316501	Salvador do Sul
43	Rio Grande do Sul	4318481	Sao Jose do Hortencio
43	Rio Grande do Sul	4318614	Sao Jose do Sul
43	Rio Grande do Sul	4319356	Sao Pedro da Serra
43	Rio Grande do Sul	4319505	Sao Sebastiao do Cai
43	Rio Grande do Sul	4319752	Sao Vendelino
43	Rio Grande do Sul	4322251	Tupandi
43	Rio Grande do Sul	4322541	Vale Real
43	Rio Grande do Sul	4304408	Canela
43	Rio Grande do Sul	4306403	Dois Irmaos
43	Rio Grande do Sul	4309100	Gramado
43	Rio Grande do Sul	4310108	Igrejinha
43	Rio Grande do Sul	4310801	Ivoti
43	Rio Grande do Sul	4311627	Lindolfo Collor
43	Rio Grande do Sul	4312476	Morro Reuter
43	Rio Grande do Sul	4313201	Nova Petropolis
43	Rio Grande do Sul	4314423	Picada Cafe
43	Rio Grande do Sul	4315149	Presidente Lucena
43	Rio Grande do Sul	4315750	Riozinho
43	Rio Grande do Sul	4316006	Rolante
43	Rio Grande do Sul	4316956	Santa Maria do Herval
43	Rio Grande do Sul	4321204	Taquara
43	Rio Grande do Sul	4321709	Tres Coroas
43	Rio Grande do Sul	4301107	Arroio dos Ratos
43	Rio Grande do Sul	4301750	Barao do Triunfo
43	Rio Grande do Sul	4302709	Butia
43	Rio Grande do Sul	4305355	Charqueadas
43	Rio Grande do Sul	4308805	General Camara
43	Rio Grande do Sul	4312252	Minas do Leao
43	Rio Grande do Sul	4318408	Sao Jeronimo
43	Rio Grande do Sul	4322004	Triunfo
43	Rio Grande do Sul	4322525	Vale Verde
43	Rio Grande do Sul	4300604	Alvorada
43	Rio Grande do Sul	4300877	Ararica
43	Rio Grande do Sul	4303103	Cachoeirinha
43	Rio Grande do Sul	4303905	Campo Bom
43	Rio Grande do Sul	4304606	Canoas
43	Rio Grande do Sul	4306767	Eldorado do Sul
43	Rio Grande do Sul	4307609	Estancia Velha
43	Rio Grande do Sul	4307708	Esteio
43	Rio Grande do Sul	4309050	Glorinha
43	Rio Grande do Sul	4309209	Gravatai
43	Rio Grande do Sul	4309308	Guaiba
43	Rio Grande do Sul	4311981	Mariana Pimentel
43	Rio Grande do Sul	4313060	Nova Hartz
43	Rio Grande do Sul	4313375	Nova Santa Rita
43	Rio Grande do Sul	4313409	Novo Hamburgo
43	Rio Grande do Sul	4314050	Parobe
43	Rio Grande do Sul	4314902	Porto Alegre
43	Rio Grande do Sul	4318705	Sao Leopoldo
43	Rio Grande do Sul	4319901	Sapiranga
43	Rio Grande do Sul	4320008	Sapucaia do Sul
43	Rio Grande do Sul	4320552	Sertao Santana
43	Rio Grande do Sul	4323002	Viamao
43	Rio Grande do Sul	4301057	Arroio do Sal
43	Rio Grande do Sul	4301636	Balneario Pinhal
43	Rio Grande do Sul	4304630	Capao da Canoa
43	Rio Grande do Sul	4304671	Capivari do Sul
43	Rio Grande do Sul	4304713	Caraa
43	Rio Grande do Sul	4305454	Cidreira
43	Rio Grande do Sul	4306551	Dom Pedro de Alcantara
43	Rio Grande do Sul	4310330	Imbe
43	Rio Grande do Sul	4310652	Itati
43	Rio Grande do Sul	4311734	Mampituba
43	Rio Grande do Sul	4311775	Maquine
43	Rio Grande do Sul	4312443	Morrinhos do Sul
43	Rio Grande do Sul	4312500	Mostardas
43	Rio Grande do Sul	4313508	Osorio
43	Rio Grande do Sul	4313656	Palmares do Sul
43	Rio Grande do Sul	4317608	Santo Antonio da Patrulha
43	Rio Grande do Sul	4321352	Tavares
43	Rio Grande do Sul	4321436	Terra de Areia
43	Rio Grande do Sul	4321501	Torres
43	Rio Grande do Sul	4321600	Tramandai
43	Rio Grande do Sul	4321667	Tres Cachoeiras
43	Rio Grande do Sul	4321832	Tres Forquilhas
43	Rio Grande do Sul	4323804	Xangri-la
43	Rio Grande do Sul	4300851	Arambare
43	Rio Grande do Sul	4301909	Barra do Ribeiro
43	Rio Grande do Sul	4303509	Camaqua
43	Rio Grande do Sul	4305173	Cerro Grande do Sul
43	Rio Grande do Sul	4305447	Chuvisca
43	Rio Grande do Sul	4306502	Dom Feliciano
43	Rio Grande do Sul	4320354	Sentinela do Sul
43	Rio Grande do Sul	4321105	Tapes
43	Rio Grande do Sul	4300406	Alegrete
43	Rio Grande do Sul	4301875	Barra do Quarai
43	Rio Grande do Sul	4308656	Garruchos
43	Rio Grande do Sul	4310603	Itaqui
43	Rio Grande do Sul	4311718	Macambara
43	Rio Grande do Sul	4311759	Manoel Viana
43	Rio Grande do Sul	4315305	Quarai
43	Rio Grande do Sul	4318002	Sao Borja
43	Rio Grande do Sul	4318101	Sao Francisco de Assis
43	Rio Grande do Sul	4322400	Uruguaiana
43	Rio Grande do Sul	4316402	Rosario do Sul
43	Rio Grande do Sul	4316972	Santa Margarida do Sul
43	Rio Grande do Sul	4317103	Santana do Livramento
43	Rio Grande do Sul	4318309	Sao Gabriel
43	Rio Grande do Sul	4300034	Acegua
43	Rio Grande do Sul	4301602	Bage
43	Rio Grande do Sul	4306601	Dom Pedrito
43	Rio Grande do Sul	4309654	Hulha Negra
43	Rio Grande do Sul	4311502	Lavras do Sul
43	Rio Grande do Sul	4300638	Amaral Ferrador
43	Rio Grande do Sul	4302808	Cacapava do Sul
43	Rio Grande do Sul	4304358	Candiota
43	Rio Grande do Sul	4306908	Encruzilhada do Sul
43	Rio Grande do Sul	4314175	Pedras Altas
43	Rio Grande do Sul	4314506	Pinheiro Machado
43	Rio Grande do Sul	4314605	Piratini
43	Rio Grande do Sul	4317004	Santana da Boa Vista
43	Rio Grande do Sul	4301073	Arroio do Padre
43	Rio Grande do Sul	4304507	Cangucu
43	Rio Grande do Sul	4304663	Capao do Leao
43	Rio Grande do Sul	4305124	Cerrito
43	Rio Grande do Sul	4306056	Cristal
43	Rio Grande do Sul	4312450	Morro Redondo
43	Rio Grande do Sul	4314209	Pedro Osorio
43	Rio Grande do Sul	4314407	Pelotas
43	Rio Grande do Sul	4318804	Sao Lourenco do Sul
43	Rio Grande do Sul	4322327	Turucu
43	Rio Grande do Sul	4301305	Arroio Grande
43	Rio Grande do Sul	4307104	Herval
43	Rio Grande do Sul	4311007	Jaguarao
43	Rio Grande do Sul	4305439	Chui
43	Rio Grande do Sul	4315602	Rio Grande
43	Rio Grande do Sul	4317301	Santa Vitoria do Palmar
43	Rio Grande do Sul	4318507	Sao Jose do Norte
50	Mato Grosso do Sul	5003207	Corumba
50	Mato Grosso do Sul	5005202	Ladario
50	Mato Grosso do Sul	5006903	Porto Murtinho
50	Mato Grosso do Sul	5000708	Anastacio
50	Mato Grosso do Sul	5001102	Aquidauana
50	Mato Grosso do Sul	5003488	Dois Irmaos do Buriti
50	Mato Grosso do Sul	5005608	Miranda
50	Mato Grosso do Sul	5000252	Alcinopolis
50	Mato Grosso do Sul	5002605	Camapua
50	Mato Grosso do Sul	5003306	Coxim
50	Mato Grosso do Sul	5003900	Figueirao
50	Mato Grosso do Sul	5006408	Pedro Gomes
50	Mato Grosso do Sul	5007406	Rio Verde de Mato Grosso
50	Mato Grosso do Sul	5007695	Sao Gabriel do Oeste
50	Mato Grosso do Sul	5007935	Sonora
50	Mato Grosso do Sul	5001508	Bandeirantes
50	Mato Grosso do Sul	5002704	Campo Grande
50	Mato Grosso do Sul	5003108	Corguinho
50	Mato Grosso do Sul	5004908	Jaraguari
50	Mato Grosso do Sul	5007307	Rio Negro
50	Mato Grosso do Sul	5007505	Rochedo
50	Mato Grosso do Sul	5007901	Sidrolandia
50	Mato Grosso do Sul	5008008	Terenos
50	Mato Grosso do Sul	5002902	Cassilandia
50	Mato Grosso do Sul	5002951	Chapadao do Sul
50	Mato Grosso do Sul	5003256	Costa Rica
50	Mato Grosso do Sul	5001003	Aparecida do Taboado
50	Mato Grosso do Sul	5004403	Inocencia
50	Mato Grosso do Sul	5006309	Paranaiba
50	Mato Grosso do Sul	5007802	Selviria
50	Mato Grosso do Sul	5000203	agua Clara
50	Mato Grosso do Sul	5002308	Brasilandia
50	Mato Grosso do Sul	5007109	Ribas do Rio Pardo
50	Mato Grosso do Sul	5007554	Santa Rita do Pardo
50	Mato Grosso do Sul	5008305	Tres Lagoas
50	Mato Grosso do Sul	5000807	Anaurilandia
50	Mato Grosso do Sul	5001904	Bataguassu
50	Mato Grosso do Sul	5002001	Bataypora
50	Mato Grosso do Sul	5006200	Nova Andradina
50	Mato Grosso do Sul	5007976	Taquarussu
50	Mato Grosso do Sul	5002100	Bela Vista
50	Mato Grosso do Sul	5002159	Bodoquena
50	Mato Grosso do Sul	5002209	Bonito
50	Mato Grosso do Sul	5002803	Caracol
50	Mato Grosso do Sul	5004106	Guia Lopes da Laguna
50	Mato Grosso do Sul	5005004	Jardim
50	Mato Grosso do Sul	5005806	Nioaque
50	Mato Grosso do Sul	5000609	Amambai
50	Mato Grosso do Sul	5000906	Antonio Joao
50	Mato Grosso do Sul	5001243	Aral Moreira
50	Mato Grosso do Sul	5002407	Caarapo
50	Mato Grosso do Sul	5003504	Douradina
50	Mato Grosso do Sul	5003702	Dourados
50	Mato Grosso do Sul	5003801	Fatima do Sul
50	Mato Grosso do Sul	5004502	Itapora
50	Mato Grosso do Sul	5005152	Juti
50	Mato Grosso do Sul	5005251	Laguna Carapa
50	Mato Grosso do Sul	5005400	Maracaju
50	Mato Grosso do Sul	5006002	Nova Alvorada do Sul
50	Mato Grosso do Sul	5006606	Ponta Pora
50	Mato Grosso do Sul	5007208	Rio Brilhante
50	Mato Grosso do Sul	5008404	Vicentina
50	Mato Grosso do Sul	5000856	Angelica
50	Mato Grosso do Sul	5003157	Coronel Sapucaia
50	Mato Grosso do Sul	5003454	Deodapolis
50	Mato Grosso do Sul	5003751	Eldorado
50	Mato Grosso do Sul	5004007	Gloria de Dourados
50	Mato Grosso do Sul	5004304	Iguatemi
50	Mato Grosso do Sul	5004601	Itaquirai
50	Mato Grosso do Sul	5004700	Ivinhema
50	Mato Grosso do Sul	5004809	Japora
50	Mato Grosso do Sul	5005103	Jatei
50	Mato Grosso do Sul	5005681	Mundo Novo
50	Mato Grosso do Sul	5005707	Navirai
50	Mato Grosso do Sul	5006259	Novo Horizonte do Sul
50	Mato Grosso do Sul	5006358	Paranhos
50	Mato Grosso do Sul	5007703	Sete Quedas
50	Mato Grosso do Sul	5007950	Tacuru
51	Mato Grosso	5101407	Aripuana
51	Mato Grosso	5101902	Brasnorte
51	Mato Grosso	5102850	Castanheira
51	Mato Grosso	5103254	Colniza
51	Mato Grosso	5103379	Cotriguacu
51	Mato Grosso	5105150	Juina
51	Mato Grosso	5105176	Juruena
51	Mato Grosso	5107578	Rondolandia
51	Mato Grosso	5100250	Alta Floresta
51	Mato Grosso	5100805	Apiacas
51	Mato Grosso	5102793	Carlinda
51	Mato Grosso	5106158	Nova Bandeirantes
51	Mato Grosso	5106299	Paranaita
51	Mato Grosso	5108956	Nova Monte Verde
51	Mato Grosso	5103205	Colider
51	Mato Grosso	5104104	Guaranta do Norte
51	Mato Grosso	5105606	Matupa
51	Mato Grosso	5106216	Nova Canaa do Norte
51	Mato Grosso	5106265	Novo Mundo
51	Mato Grosso	5106422	Peixoto de Azevedo
51	Mato Grosso	5108055	Terra Nova do Norte
51	Mato Grosso	5108808	Nova Guarita
51	Mato Grosso	5102637	Campo Novo do Parecis
51	Mato Grosso	5102686	Campos de Julio
51	Mato Grosso	5103304	Comodoro
51	Mato Grosso	5103502	Diamantino
51	Mato Grosso	5107875	Sapezal
51	Mato Grosso	5105101	Juara
51	Mato Grosso	5106273	Novo Horizonte do Norte
51	Mato Grosso	5106802	Porto dos Gauchos
51	Mato Grosso	5107305	Sao Jose do Rio Claro
51	Mato Grosso	5107941	Tabapora
51	Mato Grosso	5108907	Nova Maringa
51	Mato Grosso	5104526	Ipiranga do Norte
51	Mato Grosso	5104542	Itanhanga
51	Mato Grosso	5105259	Lucas do Rio Verde
51	Mato Grosso	5105903	Nobres
51	Mato Grosso	5106224	Nova Mutum
51	Mato Grosso	5106240	Nova Ubirata
51	Mato Grosso	5107768	Santa Rita do Trivelato
51	Mato Grosso	5107925	Sorriso
51	Mato Grosso	5108006	Tapurah
51	Mato Grosso	5103056	Claudia
51	Mato Grosso	5103700	Feliz Natal
51	Mato Grosso	5104559	Itauba
51	Mato Grosso	5105580	Marcelandia
51	Mato Grosso	5106190	Nova Santa Helena
51	Mato Grosso	5107248	Santa Carmem
51	Mato Grosso	5107909	Sinop
51	Mato Grosso	5108303	Uniao do Sul
51	Mato Grosso	5108501	Vera
51	Mato Grosso	5103858	Gaucha do Norte
51	Mato Grosso	5106208	Nova Brasilandia
51	Mato Grosso	5106307	Paranatinga
51	Mato Grosso	5106455	Planalto da Serra
51	Mato Grosso	5100359	Alto Boa Vista
51	Mato Grosso	5101852	Bom Jesus do Araguaia
51	Mato Grosso	5102694	Canabrava do Norte
51	Mato Grosso	5103353	Confresa
51	Mato Grosso	5105309	Luciara
51	Mato Grosso	5106315	Novo Santo Antonio
51	Mato Grosso	5106778	Porto Alegre do Norte
51	Mato Grosso	5107180	Ribeirao Cascalheira
51	Mato Grosso	5107354	Sao Jose do Xingu
51	Mato Grosso	5107743	Santa Cruz do Xingu
51	Mato Grosso	5107776	Santa Terezinha
51	Mato Grosso	5107859	Sao Felix do Araguaia
51	Mato Grosso	5107883	Serra Nova Dourada
51	Mato Grosso	5108600	Vila Rica
51	Mato Grosso	5100201	agua Boa
51	Mato Grosso	5102603	Campinapolis
51	Mato Grosso	5102702	Canarana
51	Mato Grosso	5106174	Nova Nazare
51	Mato Grosso	5106257	Nova Xavantina
51	Mato Grosso	5106281	Novo Sao Joaquim
51	Mato Grosso	5107065	Querencia
51	Mato Grosso	5107792	Santo Antonio do Leste
51	Mato Grosso	5101001	Araguaiana
51	Mato Grosso	5101803	Barra do Garcas
51	Mato Grosso	5103106	Cocalinho
51	Mato Grosso	5103361	Conquista D'Oeste
51	Mato Grosso	5105507	Vila Bela da Santissima Trindade
51	Mato Grosso	5106182	Nova Lacerda
51	Mato Grosso	5106752	Pontes e Lacerda
51	Mato Grosso	5108352	Vale de Sao Domingos
51	Mato Grosso	5101704	Barra do Bugres
51	Mato Grosso	5103452	Denise
51	Mato Grosso	5106232	Nova Olimpia
51	Mato Grosso	5106851	Porto Estrela
51	Mato Grosso	5107958	Tangara da Serra
51	Mato Grosso	5101258	Araputanga
51	Mato Grosso	5103809	Figueiropolis D'Oeste
51	Mato Grosso	5103957	Gloria D'Oeste
51	Mato Grosso	5104500	Indiavai
51	Mato Grosso	5105002	Jauru
51	Mato Grosso	5105234	Lambari D'Oeste
51	Mato Grosso	5105622	Mirassol d'Oeste
51	Mato Grosso	5106828	Porto Esperidiao
51	Mato Grosso	5107107	Sao Jose dos Quatro Marcos
51	Mato Grosso	5107156	Reserva do Cabacal
51	Mato Grosso	5107206	Rio Branco
51	Mato Grosso	5107750	Salto do Ceu
51	Mato Grosso	5100508	Alto Paraguai
51	Mato Grosso	5101308	Arenapolis
51	Mato Grosso	5106000	Nortelandia
51	Mato Grosso	5107263	Santo Afonso
51	Mato Grosso	5108857	Nova Marilandia
51	Mato Grosso	5100102	Acorizal
51	Mato Grosso	5104906	Jangada
51	Mato Grosso	5107701	Rosario Oeste
51	Mato Grosso	5103007	Chapada dos Guimaraes
51	Mato Grosso	5103403	Cuiaba
51	Mato Grosso	5106109	Nossa Senhora do Livramento
51	Mato Grosso	5107800	Santo Antonio do Leverger
51	Mato Grosso	5108402	Varzea Grande
51	Mato Grosso	5101605	Barao de Melgaco
51	Mato Grosso	5102504	Caceres
51	Mato Grosso	5103437	Curvelandia
51	Mato Grosso	5106505	Pocone
51	Mato Grosso	5102678	Campo Verde
51	Mato Grosso	5107040	Primavera do Leste
51	Mato Grosso	5101209	Araguainha
51	Mato Grosso	5103908	General Carneiro
51	Mato Grosso	5104203	Guiratinga
51	Mato Grosso	5106653	Pontal do Araguaia
51	Mato Grosso	5106703	Ponte Branca
51	Mato Grosso	5107008	Poxoreo
51	Mato Grosso	5107198	Ribeiraozinho
51	Mato Grosso	5108105	Tesouro
51	Mato Grosso	5108204	Torixoreu
51	Mato Grosso	5103601	Dom Aquino
51	Mato Grosso	5104609	Itiquira
51	Mato Grosso	5104807	Jaciara
51	Mato Grosso	5105200	Juscimeira
51	Mato Grosso	5106372	Pedra Preta
51	Mato Grosso	5107297	Sao Jose do Povo
51	Mato Grosso	5107404	Sao Pedro da Cipa
51	Mato Grosso	5107602	Rondonopolis
51	Mato Grosso	5100300	Alto Araguaia
51	Mato Grosso	5100409	Alto Garcas
51	Mato Grosso	5100607	Alto Taquari
52	Goias	5206404	Crixas
52	Goias	5214002	Mozarlandia
52	Goias	5214051	Mundo Novo
52	Goias	5214838	Nova Crixas
52	Goias	5215256	Novo Planalto
52	Goias	5220207	Sao Miguel do Araguaia
52	Goias	5221577	Uirapuru
52	Goias	5202155	Araguapaz
52	Goias	5202502	Aruana
52	Goias	5203807	Britania
52	Goias	5207535	Faina
52	Goias	5208905	Goias
52	Goias	5211008	Itapirapua
52	Goias	5212204	Jussara
52	Goias	5212956	Matrincha
52	Goias	5219258	Santa Fe de Goias
52	Goias	5201702	Aragarcas
52	Goias	5202353	Arenopolis
52	Goias	5203104	Baliza
52	Goias	5203401	Bom Jardim de Goias
52	Goias	5207105	Diorama
52	Goias	5213707	Montes Claros de Goias
52	Goias	5217203	Piranhas
52	Goias	5200555	Alto Horizonte
52	Goias	5200829	Amaralina
52	Goias	5203575	Bonopolis
52	Goias	5204656	Campinacu
52	Goias	5204706	Campinorte
52	Goias	5204953	Campos Verdes
52	Goias	5207501	Estrela do Norte
52	Goias	5208103	Formoso
52	Goias	5212808	Mara Rosa
52	Goias	5213087	Minacu
52	Goias	5213772	Montividiu do Norte
52	Goias	5214101	Mutunopolis
52	Goias	5214606	Niquelandia
52	Goias	5214879	Nova Iguacu de Goias
52	Goias	5218003	Porangatu
52	Goias	5219605	Santa Tereza de Goias
52	Goias	5219704	Santa Terezinha de Goias
52	Goias	5221452	Trombas
52	Goias	5221601	Uruacu
52	Goias	5200605	Alto Paraiso de Goias
52	Goias	5204904	Campos Belos
52	Goias	5205307	Cavalcante
52	Goias	5205521	Colinas do Sul
52	Goias	5213509	Monte Alegre de Goias
52	Goias	5214903	Nova Roma
52	Goias	5220009	Sao Joao d'Alianca
52	Goias	5221080	Teresina de Goias
52	Goias	5203203	Barro Alto
52	Goias	5205000	Carmo do Rio Verde
52	Goias	5205406	Ceres
52	Goias	5208608	Goianesia
52	Goias	5209291	Guaraita
52	Goias	5209457	Guarinos
52	Goias	5209804	Hidrolina
52	Goias	5210158	Ipiranga de Goias
52	Goias	5210901	Itapaci
52	Goias	5211206	Itapuranga
52	Goias	5213855	Morro Agudo de Goias
52	Goias	5214705	Nova America
52	Goias	5214861	Nova Gloria
52	Goias	5216908	Pilar de Goias
52	Goias	5218607	Rialma
52	Goias	5218706	Rianapolis
52	Goias	5218904	Rubiataba
52	Goias	5219357	Santa Isabel
52	Goias	5219456	Santa Rita do Novo Destino
52	Goias	5220157	Sao Luiz do Norte
52	Goias	5220280	Sao Patricio
52	Goias	5221700	Uruana
52	Goias	5201108	Anapolis
52	Goias	5201603	Aracu
52	Goias	5203609	Brazabrantes
52	Goias	5204854	Campo Limpo de Goias
52	Goias	5205208	Caturai
52	Goias	5206800	Damolandia
52	Goias	5209606	Heitorai
52	Goias	5210000	Inhumas
52	Goias	5210406	Itaberai
52	Goias	5210562	Itaguari
52	Goias	5210604	Itaguaru
52	Goias	5211404	Itaucu
52	Goias	5211800	Jaragua
52	Goias	5212055	Jesupolis
52	Goias	5215009	Nova Veneza
52	Goias	5215405	Ouro Verde de Goias
52	Goias	5216809	Petrolina de Goias
52	Goias	5219506	Santa Rosa de Goias
52	Goias	5219902	Sao Francisco de Goias
52	Goias	5221007	Taquaral de Goias
52	Goias	5200902	Amorinopolis
52	Goias	5204201	Cachoeira de Goias
52	Goias	5205703	Corrego do Ouro
52	Goias	5207600	Fazenda Nova
52	Goias	5210208	Ipora
52	Goias	5210307	Israelandia
52	Goias	5211602	Ivolandia
52	Goias	5212006	Jaupaci
52	Goias	5213400	Moipora
52	Goias	5215207	Novo Brasil
52	Goias	5200159	Adelandia
52	Goias	5200852	Americano do Brasil
52	Goias	5201306	Anicuns
52	Goias	5202601	Aurilandia
52	Goias	5202809	Avelinopolis
52	Goias	5203939	Buriti de Goias
52	Goias	5207808	Firminopolis
52	Goias	5213905	Mossamedes
52	Goias	5214408	Nazario
52	Goias	5219001	Sanclerlandia
52	Goias	5219100	Santa Barbara de Goias
52	Goias	5220108	Sao Luis de Montes Belos
52	Goias	5221502	Turvania
52	Goias	5200050	Abadia de Goias
52	Goias	5201405	Aparecida de Goiania
52	Goias	5201801	Aragoiania
52	Goias	5203302	Bela Vista de Goias
52	Goias	5203559	Bonfinopolis
52	Goias	5204557	Caldazinha
52	Goias	5208400	Goianapolis
52	Goias	5208707	Goiania
52	Goias	5208806	Goianira
52	Goias	5209200	Guapo
52	Goias	5209705	Hidrolandia
52	Goias	5212303	Leopoldo de Bulhoes
52	Goias	5214507	Neropolis
52	Goias	5219738	Santo Antonio de Goias
52	Goias	5220454	Senador Canedo
52	Goias	5221197	Terezopolis de Goias
52	Goias	5221403	Trindade
52	Goias	5200803	Alvorada do Norte
52	Goias	5203962	Buritinopolis
52	Goias	5206701	Damianopolis
52	Goias	5207907	Flores de Goias
52	Goias	5208301	Divinopolis de Goias
52	Goias	5209408	Guarani de Goias
52	Goias	5209903	Iaciara
52	Goias	5212709	Mambai
52	Goias	5218300	Posse
52	Goias	5219803	Sao Domingos
52	Goias	5220686	Simolandia
52	Goias	5220702	Sitio d'Abadia
52	Goias	5200100	Abadiania
52	Goias	5200175	agua Fria de Goias
52	Goias	5200258	aguas Lindas de Goias
52	Goias	5200308	Alexania
52	Goias	5204003	Cabeceiras
52	Goias	5205497	Cidade Ocidental
52	Goias	5205513	Cocalzinho de Goias
52	Goias	5205802	Corumba de Goias
52	Goias	5206206	Cristalina
52	Goias	5208004	Formosa
52	Goias	5212501	Luziania
52	Goias	5213053	Mimoso de Goias
52	Goias	5215231	Novo Gama
52	Goias	5215603	Padre Bernardo
52	Goias	5217302	Pirenopolis
52	Goias	5217609	Planaltina
52	Goias	5219753	Santo Antonio do Descoberto
52	Goias	5221858	Valparaiso de Goias
52	Goias	5222203	Vila Boa
52	Goias	5222302	Vila Propicio
52	Goias	5201454	Aparecida do Rio Doce
52	Goias	5201504	Apore
52	Goias	5204409	Caiaponia
52	Goias	5205059	Castelandia
52	Goias	5205471	Chapadao do Ceu
52	Goias	5207253	Doverlandia
52	Goias	5211909	Jatai
52	Goias	5213004	Maurilandia
52	Goias	5213103	Mineiros
52	Goias	5213756	Montividiu
52	Goias	5215652	Palestina de Goias
52	Goias	5216452	Perolandia
52	Goias	5218102	Portelandia
52	Goias	5218805	Rio Verde
52	Goias	5219308	Santa Helena de Goias
52	Goias	5219407	Santa Rita do Araguaia
52	Goias	5219712	Santo Antonio da Barra
52	Goias	5220504	Serranopolis
52	Goias	5200134	Acreuna
52	Goias	5204607	Campestre de Goias
52	Goias	5205455	Cezarina
52	Goias	5207352	Edealina
52	Goias	5207402	Edeia
52	Goias	5209952	Indiara
52	Goias	5211701	Jandaia
52	Goias	5215702	Palmeiras de Goias
52	Goias	5215900	Palminopolis
52	Goias	5216403	Parauna
52	Goias	5220058	Sao Joao da Parauna
52	Goias	5221551	Turvelandia
52	Goias	5221908	Varjao
52	Goias	5200209	agua Limpa
52	Goias	5200506	Aloandia
52	Goias	5203500	Bom Jesus de Goias
52	Goias	5203906	Buriti Alegre
52	Goias	5204250	Cachoeira Dourada
52	Goias	5204508	Caldas Novas
52	Goias	5206503	Crominia
52	Goias	5209101	Goiatuba
52	Goias	5209937	Inaciolandia
52	Goias	5211503	Itumbiara
52	Goias	5212105	Joviania
52	Goias	5212600	Mairipotaba
52	Goias	5212907	Marzagao
52	Goias	5213806	Morrinhos
52	Goias	5216007	Panama
52	Goias	5217104	Piracanjuba
52	Goias	5217708	Pontalina
52	Goias	5218052	Porteirao
52	Goias	5218391	Professor Jamil
52	Goias	5218789	Rio Quente
52	Goias	5222054	Vicentinopolis
52	Goias	5206305	Cristianopolis
52	Goias	5208152	Gameleira de Goias
52	Goias	5215306	Orizona
52	Goias	5215801	Palmelo
52	Goias	5217401	Pires do Rio
52	Goias	5219209	Santa Cruz de Goias
52	Goias	5220264	Sao Miguel do Passa Quatro
52	Goias	5220603	Silvania
52	Goias	5221809	Urutai
52	Goias	5222005	Vianopolis
52	Goias	5201207	Anhanguera
52	Goias	5204805	Campo Alegre de Goias
52	Goias	5205109	Catalao
52	Goias	5205901	Corumbaiba
52	Goias	5206602	Cumari
52	Goias	5206909	Davinopolis
52	Goias	5208509	Goiandira
52	Goias	5210109	Ipameri
52	Goias	5214804	Nova Aurora
52	Goias	5215504	Ouvidor
52	Goias	5221304	Tres Ranchos
52	Goias	5204102	Cachoeira Alta
52	Goias	5204300	Cacu
52	Goias	5209150	Gouvelandia
52	Goias	5210802	Itaja
52	Goias	5211305	Itaruma
52	Goias	5212253	Lagoa Santa
52	Goias	5216304	Paranaiguara
52	Goias	5218508	Quirinopolis
52	Goias	5220405	Sao Simao
53	Distrito Federal	5300108	Brasilia
\.

CREATE INDEX nfe_city_name_state_code_idx  ON
        nfe_city_data (city_name, state_code);


