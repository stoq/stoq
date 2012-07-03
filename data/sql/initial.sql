-- Insert our brazilian city list. There's no need to check for existing
-- cities because, this will be used on a fresh database.
-- This data was adapted from:
--   http://www.sped.fazenda.gov.br/spedtabelas/AppConsulta/publico/aspx/ConsultaTabelasExternas.aspx?CodSistema=SpedFiscal
COPY city_location
(country, state_code, state, city_code, city) FROM stdin;
Brazil	53	DF	5300108	Brasília
Brazil	14	RR	1400050	Alto Alegre
Brazil	14	RR	1400027	Amajari
Brazil	14	RR	1400100	Boa Vista
Brazil	14	RR	1400159	Bonfim
Brazil	14	RR	1400175	Cantá
Brazil	14	RR	1400209	Caracaraí
Brazil	14	RR	1400233	Caroebe
Brazil	14	RR	1400282	Iracema
Brazil	14	RR	1400308	Mucajaí
Brazil	14	RR	1400407	Normandia
Brazil	14	RR	1400456	Pacaraima
Brazil	14	RR	1400472	Rorainópolis
Brazil	14	RR	1400506	São João da Baliza
Brazil	14	RR	1400605	São Luiz
Brazil	14	RR	1400704	Uiramutã
Brazil	16	AP	1600105	Amapá
Brazil	16	AP	1600204	Calçoene
Brazil	16	AP	1600212	Cutias
Brazil	16	AP	1600238	Ferreira Gomes
Brazil	16	AP	1600253	Itaubal
Brazil	16	AP	1600279	Laranjal do Jari
Brazil	16	AP	1600303	Macapá
Brazil	16	AP	1600402	Mazagão
Brazil	16	AP	1600501	Oiapoque
Brazil	16	AP	1600154	Pedra Branca do Amapari
Brazil	16	AP	1600535	Porto Grande
Brazil	16	AP	1600550	Pracuúba
Brazil	16	AP	1600600	Santana
Brazil	16	AP	1600055	Serra do Navio
Brazil	16	AP	1600709	Tartarugalzinho
Brazil	16	AP	1600808	Vitória do Jari
Brazil	12	AC	1200013	Acrelândia
Brazil	12	AC	1200054	Assis Brasil
Brazil	12	AC	1200104	Brasiléia
Brazil	12	AC	1200138	Bujari
Brazil	12	AC	1200179	Capixaba
Brazil	12	AC	1200203	Cruzeiro do Sul
Brazil	12	AC	1200252	Epitaciolândia
Brazil	12	AC	1200302	Feijó
Brazil	12	AC	1200328	Jordão
Brazil	12	AC	1200336	Mâncio Lima
Brazil	12	AC	1200344	Manoel Urbano
Brazil	12	AC	1200351	Marechal Thaumaturgo
Brazil	12	AC	1200385	Plácido de Castro
Brazil	12	AC	1200807	Porto Acre
Brazil	12	AC	1200393	Porto Walter
Brazil	12	AC	1200401	Rio Branco
Brazil	12	AC	1200427	Rodrigues Alves
Brazil	12	AC	1200435	Santa Rosa do Purus
Brazil	12	AC	1200500	Sena Madureira
Brazil	12	AC	1200450	Senador Guiomard
Brazil	12	AC	1200609	Tarauacá
Brazil	12	AC	1200708	Xapuri
Brazil	11	RO	1100015	Alta Floresta D'Oeste
Brazil	11	RO	1100379	Alto Alegre dos Parecis
Brazil	11	RO	1100403	Alto Paraíso
Brazil	11	RO	1100346	Alvorada D'Oeste
Brazil	11	RO	1100023	Ariquemes
Brazil	11	RO	1100452	Buritis
Brazil	11	RO	1100031	Cabixi
Brazil	11	RO	1100601	Cacaulândia
Brazil	11	RO	1100049	Cacoal
Brazil	11	RO	1100700	Campo Novo de Rondônia
Brazil	11	RO	1100809	Candeias do Jamari
Brazil	11	RO	1100908	Castanheiras
Brazil	11	RO	1100056	Cerejeiras
Brazil	11	RO	1100924	Chupinguaia
Brazil	11	RO	1100064	Colorado do Oeste
Brazil	11	RO	1100072	Corumbiara
Brazil	11	RO	1100080	Costa Marques
Brazil	11	RO	1100940	Cujubim
Brazil	11	RO	1100098	Espigão D'Oeste
Brazil	11	RO	1101005	Governador Jorge Teixeira
Brazil	11	RO	1100106	Guajará-Mirim
Brazil	11	RO	1101104	Itapuã do Oeste
Brazil	11	RO	1100114	Jaru
Brazil	11	RO	1100122	Ji-Paraná
Brazil	11	RO	1100130	Machadinho D'Oeste
Brazil	11	RO	1101203	Ministro Andreazza
Brazil	11	RO	1101302	Mirante da Serra
Brazil	11	RO	1101401	Monte Negro
Brazil	11	RO	1100148	Nova Brasilândia D'Oeste
Brazil	11	RO	1100338	Nova Mamoré
Brazil	11	RO	1101435	Nova União
Brazil	11	RO	1100502	Novo Horizonte do Oeste
Brazil	11	RO	1100155	Ouro Preto do Oeste
Brazil	11	RO	1101450	Parecis
Brazil	11	RO	1100189	Pimenta Bueno
Brazil	11	RO	1101468	Pimenteiras do Oeste
Brazil	11	RO	1100205	Porto Velho
Brazil	11	RO	1100254	Presidente Médici
Brazil	11	RO	1101476	Primavera de Rondônia
Brazil	11	RO	1100262	Rio Crespo
Brazil	11	RO	1100288	Rolim de Moura
Brazil	11	RO	1100296	Santa Luzia D'Oeste
Brazil	11	RO	1101484	São Felipe D'Oeste
Brazil	11	RO	1101492	São Francisco do Guaporé
Brazil	11	RO	1100320	São Miguel do Guaporé
Brazil	11	RO	1101500	Seringueiras
Brazil	11	RO	1101559	Teixeirópolis
Brazil	11	RO	1101609	Theobroma
Brazil	11	RO	1101708	Urupá
Brazil	11	RO	1101757	Vale do Anari
Brazil	11	RO	1101807	Vale do Paraíso
Brazil	11	RO	1100304	Vilhena
Brazil	13	AM	1300029	Alvarães
Brazil	13	AM	1300060	Amaturá
Brazil	13	AM	1300086	Anamã
Brazil	13	AM	1300102	Anori
Brazil	13	AM	1300144	Apuí
Brazil	13	AM	1300201	Atalaia do Norte
Brazil	13	AM	1300300	Autazes
Brazil	13	AM	1300409	Barcelos
Brazil	13	AM	1300508	Barreirinha
Brazil	13	AM	1300607	Benjamin Constant
Brazil	13	AM	1300631	Beruri
Brazil	13	AM	1300680	Boa Vista do Ramos
Brazil	13	AM	1300706	Boca do Acre
Brazil	13	AM	1300805	Borba
Brazil	13	AM	1300839	Caapiranga
Brazil	13	AM	1300904	Canutama
Brazil	13	AM	1301001	Carauari
Brazil	13	AM	1301100	Careiro
Brazil	13	AM	1301159	Careiro da Várzea
Brazil	13	AM	1301209	Coari
Brazil	13	AM	1301308	Codajás
Brazil	13	AM	1301407	Eirunepé
Brazil	13	AM	1301506	Envira
Brazil	13	AM	1301605	Fonte Boa
Brazil	13	AM	1301654	Guajará
Brazil	13	AM	1301704	Humaitá
Brazil	13	AM	1301803	Ipixuna
Brazil	13	AM	1301852	Iranduba
Brazil	13	AM	1301902	Itacoatiara
Brazil	13	AM	1301951	Itamarati
Brazil	13	AM	1302009	Itapiranga
Brazil	13	AM	1302108	Japurá
Brazil	13	AM	1302207	Juruá
Brazil	13	AM	1302306	Jutaí
Brazil	13	AM	1302405	Lábrea
Brazil	13	AM	1302504	Manacapuru
Brazil	13	AM	1302553	Manaquiri
Brazil	13	AM	1302603	Manaus
Brazil	13	AM	1302702	Manicoré
Brazil	13	AM	1302801	Maraã
Brazil	13	AM	1302900	Maués
Brazil	13	AM	1303007	Nhamundá
Brazil	13	AM	1303106	Nova Olinda do Norte
Brazil	13	AM	1303205	Novo Airão
Brazil	13	AM	1303304	Novo Aripuanã
Brazil	13	AM	1303403	Parintins
Brazil	13	AM	1303502	Pauini
Brazil	13	AM	1303536	Presidente Figueiredo
Brazil	13	AM	1303569	Rio Preto da Eva
Brazil	13	AM	1303601	Santa Isabel do Rio Negro
Brazil	13	AM	1303700	Santo Antônio do Içá
Brazil	13	AM	1303809	São Gabriel da Cachoeira
Brazil	13	AM	1303908	São Paulo de Olivença
Brazil	13	AM	1303957	São Sebastião do Uatumã
Brazil	13	AM	1304005	Silves
Brazil	13	AM	1304062	Tabatinga
Brazil	13	AM	1304104	Tapauá
Brazil	13	AM	1304203	Tefé
Brazil	13	AM	1304237	Tonantins
Brazil	13	AM	1304260	Uarini
Brazil	13	AM	1304302	Urucará
Brazil	13	AM	1304401	Urucurituba
Brazil	28	SE	2800100	Amparo de São Francisco
Brazil	28	SE	2800209	Aquidabã
Brazil	28	SE	2800308	Aracaju
Brazil	28	SE	2800407	Arauá
Brazil	28	SE	2800506	Areia Branca
Brazil	28	SE	2800605	Barra dos Coqueiros
Brazil	28	SE	2800670	Boquim
Brazil	28	SE	2800704	Brejo Grande
Brazil	28	SE	2801009	Campo do Brito
Brazil	28	SE	2801108	Canhoba
Brazil	28	SE	2801207	Canindé de São Francisco
Brazil	28	SE	2801306	Capela
Brazil	28	SE	2801405	Carira
Brazil	28	SE	2801504	Carmópolis
Brazil	28	SE	2801603	Cedro de São João
Brazil	28	SE	2801702	Cristinápolis
Brazil	28	SE	2801900	Cumbe
Brazil	28	SE	2802007	Divina Pastora
Brazil	28	SE	2802106	Estância
Brazil	28	SE	2802205	Feira Nova
Brazil	28	SE	2802304	Frei Paulo
Brazil	28	SE	2802403	Gararu
Brazil	28	SE	2802502	General Maynard
Brazil	28	SE	2802601	Gracho Cardoso
Brazil	28	SE	2802700	Ilha das Flores
Brazil	28	SE	2802809	Indiaroba
Brazil	28	SE	2802908	Itabaiana
Brazil	28	SE	2803005	Itabaianinha
Brazil	28	SE	2803104	Itabi
Brazil	28	SE	2803203	Itaporanga d'Ajuda
Brazil	28	SE	2803302	Japaratuba
Brazil	28	SE	2803401	Japoatã
Brazil	28	SE	2803500	Lagarto
Brazil	28	SE	2803609	Laranjeiras
Brazil	28	SE	2803708	Macambira
Brazil	28	SE	2803807	Malhada dos Bois
Brazil	28	SE	2803906	Malhador
Brazil	28	SE	2804003	Maruim
Brazil	28	SE	2804102	Moita Bonita
Brazil	28	SE	2804201	Monte Alegre de Sergipe
Brazil	28	SE	2804300	Muribeca
Brazil	28	SE	2804409	Neópolis
Brazil	28	SE	2804458	Nossa Senhora Aparecida
Brazil	28	SE	2804508	Nossa Senhora da Glória
Brazil	28	SE	2804607	Nossa Senhora das Dores
Brazil	28	SE	2804706	Nossa Senhora de Lourdes
Brazil	28	SE	2804805	Nossa Senhora do Socorro
Brazil	28	SE	2804904	Pacatuba
Brazil	28	SE	2805000	Pedra Mole
Brazil	28	SE	2805109	Pedrinhas
Brazil	28	SE	2805208	Pinhão
Brazil	28	SE	2805307	Pirambu
Brazil	28	SE	2805406	Poço Redondo
Brazil	28	SE	2805505	Poço Verde
Brazil	28	SE	2805604	Porto da Folha
Brazil	28	SE	2805703	Propriá
Brazil	28	SE	2805802	Riachão do Dantas
Brazil	28	SE	2805901	Riachuelo
Brazil	28	SE	2806008	Ribeirópolis
Brazil	28	SE	2806107	Rosário do Catete
Brazil	28	SE	2806206	Salgado
Brazil	28	SE	2806305	Santa Luzia do Itanhy
Brazil	28	SE	2806503	Santa Rosa de Lima
Brazil	28	SE	2806404	Santana do São Francisco
Brazil	28	SE	2806602	Santo Amaro das Brotas
Brazil	28	SE	2806701	São Cristóvão
Brazil	28	SE	2806800	São Domingos
Brazil	28	SE	2806909	São Francisco
Brazil	28	SE	2807006	São Miguel do Aleixo
Brazil	28	SE	2807105	Simão Dias
Brazil	28	SE	2807204	Siriri
Brazil	28	SE	2807303	Telha
Brazil	28	SE	2807402	Tobias Barreto
Brazil	28	SE	2807501	Tomar do Geru
Brazil	28	SE	2807600	Umbaúba
Brazil	32	ES	3200102	Afonso Cláudio
Brazil	32	ES	3200169	Água Doce do Norte
Brazil	32	ES	3200136	Águia Branca
Brazil	32	ES	3200201	Alegre
Brazil	32	ES	3200300	Alfredo Chaves
Brazil	32	ES	3200359	Alto Rio Novo
Brazil	32	ES	3200409	Anchieta
Brazil	32	ES	3200508	Apiacá
Brazil	32	ES	3200607	Aracruz
Brazil	32	ES	3200706	Atilio Vivacqua
Brazil	32	ES	3200805	Baixo Guandu
Brazil	32	ES	3200904	Barra de São Francisco
Brazil	32	ES	3201001	Boa Esperança
Brazil	32	ES	3201100	Bom Jesus do Norte
Brazil	32	ES	3201159	Brejetuba
Brazil	32	ES	3201209	Cachoeiro de Itapemirim
Brazil	32	ES	3201308	Cariacica
Brazil	32	ES	3201407	Castelo
Brazil	32	ES	3201506	Colatina
Brazil	32	ES	3201605	Conceição da Barra
Brazil	32	ES	3201704	Conceição do Castelo
Brazil	32	ES	3201803	Divino de São Lourenço
Brazil	32	ES	3201902	Domingos Martins
Brazil	32	ES	3202009	Dores do Rio Preto
Brazil	32	ES	3202108	Ecoporanga
Brazil	32	ES	3202207	Fundão
Brazil	32	ES	3202256	Governador Lindenberg
Brazil	32	ES	3202306	Guaçuí
Brazil	32	ES	3202405	Guarapari
Brazil	32	ES	3202454	Ibatiba
Brazil	32	ES	3202504	Ibiraçu
Brazil	32	ES	3202553	Ibitirama
Brazil	32	ES	3202603	Iconha
Brazil	32	ES	3202652	Irupi
Brazil	32	ES	3202702	Itaguaçu
Brazil	32	ES	3202801	Itapemirim
Brazil	32	ES	3202900	Itarana
Brazil	32	ES	3203007	Iúna
Brazil	32	ES	3203056	Jaguaré
Brazil	32	ES	3203106	Jerônimo Monteiro
Brazil	32	ES	3203130	João Neiva
Brazil	32	ES	3203163	Laranja da Terra
Brazil	32	ES	3203205	Linhares
Brazil	32	ES	3203304	Mantenópolis
Brazil	32	ES	3203320	Marataízes
Brazil	32	ES	3203346	Marechal Floriano
Brazil	32	ES	3203353	Marilândia
Brazil	32	ES	3203403	Mimoso do Sul
Brazil	32	ES	3203502	Montanha
Brazil	32	ES	3203601	Mucurici
Brazil	32	ES	3203700	Muniz Freire
Brazil	32	ES	3203809	Muqui
Brazil	32	ES	3203908	Nova Venécia
Brazil	32	ES	3204005	Pancas
Brazil	32	ES	3204054	Pedro Canário
Brazil	32	ES	3204104	Pinheiros
Brazil	32	ES	3204203	Piúma
Brazil	32	ES	3204252	Ponto Belo
Brazil	32	ES	3204302	Presidente Kennedy
Brazil	32	ES	3204351	Rio Bananal
Brazil	32	ES	3204401	Rio Novo do Sul
Brazil	32	ES	3204500	Santa Leopoldina
Brazil	32	ES	3204559	Santa Maria de Jetibá
Brazil	32	ES	3204609	Santa Teresa
Brazil	32	ES	3204658	São Domingos do Norte
Brazil	32	ES	3204708	São Gabriel da Palha
Brazil	32	ES	3204807	São José do Calçado
Brazil	32	ES	3204906	São Mateus
Brazil	32	ES	3204955	São Roque do Canaã
Brazil	32	ES	3205002	Serra
Brazil	32	ES	3205010	Sooretama
Brazil	32	ES	3205036	Vargem Alta
Brazil	32	ES	3205069	Venda Nova do Imigrante
Brazil	32	ES	3205101	Viana
Brazil	32	ES	3205150	Vila Pavão
Brazil	32	ES	3205176	Vila Valério
Brazil	32	ES	3205200	Vila Velha
Brazil	32	ES	3205309	Vitória
Brazil	50	MS	5000203	Água Clara
Brazil	50	MS	5000252	Alcinópolis
Brazil	50	MS	5000609	Amambaí
Brazil	50	MS	5000708	Anastácio
Brazil	50	MS	5000807	Anaurilândia
Brazil	50	MS	5000856	Angélica
Brazil	50	MS	5000906	Antônio João
Brazil	50	MS	5001003	Aparecida do Taboado
Brazil	50	MS	5001102	Aquidauana
Brazil	50	MS	5001243	Aral Moreira
Brazil	50	MS	5001508	Bandeirantes
Brazil	50	MS	5001904	Bataguassu
Brazil	50	MS	5002001	Batayporã
Brazil	50	MS	5002100	Bela Vista
Brazil	50	MS	5002159	Bodoquena
Brazil	50	MS	5002209	Bonito
Brazil	50	MS	5002308	Brasilândia
Brazil	50	MS	5002407	Caarapó
Brazil	50	MS	5002605	Camapuã
Brazil	50	MS	5002704	Campo Grande
Brazil	50	MS	5002803	Caracol
Brazil	50	MS	5002902	Cassilândia
Brazil	50	MS	5002951	Chapadão do Sul
Brazil	50	MS	5003108	Corguinho
Brazil	50	MS	5003157	Coronel Sapucaia
Brazil	50	MS	5003207	Corumbá
Brazil	50	MS	5003256	Costa Rica
Brazil	50	MS	5003306	Coxim
Brazil	50	MS	5003454	Deodápolis
Brazil	50	MS	5003488	Dois Irmãos do Buriti
Brazil	50	MS	5003504	Douradina
Brazil	50	MS	5003702	Dourados
Brazil	50	MS	5003751	Eldorado
Brazil	50	MS	5003801	Fátima do Sul
Brazil	50	MS	5003900	Figueirão
Brazil	50	MS	5004007	Glória de Dourados
Brazil	50	MS	5004106	Guia Lopes da Laguna
Brazil	50	MS	5004304	Iguatemi
Brazil	50	MS	5004403	Inocência
Brazil	50	MS	5004502	Itaporã
Brazil	50	MS	5004601	Itaquiraí
Brazil	50	MS	5004700	Ivinhema
Brazil	50	MS	5004809	Japorã
Brazil	50	MS	5004908	Jaraguari
Brazil	50	MS	5005004	Jardim
Brazil	50	MS	5005103	Jateí
Brazil	50	MS	5005152	Juti
Brazil	50	MS	5005202	Ladário
Brazil	50	MS	5005251	Laguna Carapã
Brazil	50	MS	5005400	Maracaju
Brazil	50	MS	5005608	Miranda
Brazil	50	MS	5005681	Mundo Novo
Brazil	50	MS	5005707	Naviraí
Brazil	50	MS	5005806	Nioaque
Brazil	50	MS	5006002	Nova Alvorada do Sul
Brazil	50	MS	5006200	Nova Andradina
Brazil	50	MS	5006259	Novo Horizonte do Sul
Brazil	50	MS	5006309	Paranaíba
Brazil	50	MS	5006358	Paranhos
Brazil	50	MS	5006408	Pedro Gomes
Brazil	50	MS	5006606	Ponta Porã
Brazil	50	MS	5006903	Porto Murtinho
Brazil	50	MS	5007109	Ribas do Rio Pardo
Brazil	50	MS	5007208	Rio Brilhante
Brazil	50	MS	5007307	Rio Negro
Brazil	50	MS	5007406	Rio Verde de Mato Grosso
Brazil	50	MS	5007505	Rochedo
Brazil	50	MS	5007554	Santa Rita do Pardo
Brazil	50	MS	5007695	São Gabriel do Oeste
Brazil	50	MS	5007802	Selvíria
Brazil	50	MS	5007703	Sete Quedas
Brazil	50	MS	5007901	Sidrolândia
Brazil	50	MS	5007935	Sonora
Brazil	50	MS	5007950	Tacuru
Brazil	50	MS	5007976	Taquarussu
Brazil	50	MS	5008008	Terenos
Brazil	50	MS	5008305	Três Lagoas
Brazil	50	MS	5008404	Vicentina
Brazil	33	RJ	3300100	Angra dos Reis
Brazil	33	RJ	3300159	Aperibé
Brazil	33	RJ	3300209	Araruama
Brazil	33	RJ	3300225	Areal
Brazil	33	RJ	3300233	Armação dos Búzios
Brazil	33	RJ	3300258	Arraial do Cabo
Brazil	33	RJ	3300308	Barra do Piraí
Brazil	33	RJ	3300407	Barra Mansa
Brazil	33	RJ	3300456	Belford Roxo
Brazil	33	RJ	3300506	Bom Jardim
Brazil	33	RJ	3300605	Bom Jesus do Itabapoana
Brazil	33	RJ	3300704	Cabo Frio
Brazil	33	RJ	3300803	Cachoeiras de Macacu
Brazil	33	RJ	3300902	Cambuci
Brazil	33	RJ	3301009	Campos dos Goytacazes
Brazil	33	RJ	3301108	Cantagalo
Brazil	33	RJ	3300936	Carapebus
Brazil	33	RJ	3301157	Cardoso Moreira
Brazil	33	RJ	3301207	Carmo
Brazil	33	RJ	3301306	Casimiro de Abreu
Brazil	33	RJ	3300951	Comendador Levy Gasparian
Brazil	33	RJ	3301405	Conceição de Macabu
Brazil	33	RJ	3301504	Cordeiro
Brazil	33	RJ	3301603	Duas Barras
Brazil	33	RJ	3301702	Duque de Caxias
Brazil	33	RJ	3301801	Engenheiro Paulo de Frontin
Brazil	33	RJ	3301850	Guapimirim
Brazil	33	RJ	3301876	Iguaba Grande
Brazil	33	RJ	3301900	Itaboraí
Brazil	33	RJ	3302007	Itaguaí
Brazil	33	RJ	3302056	Italva
Brazil	33	RJ	3302106	Itaocara
Brazil	33	RJ	3302205	Itaperuna
Brazil	33	RJ	3302254	Itatiaia
Brazil	33	RJ	3302270	Japeri
Brazil	33	RJ	3302304	Laje do Muriaé
Brazil	33	RJ	3302403	Macaé
Brazil	33	RJ	3302452	Macuco
Brazil	33	RJ	3302502	Magé
Brazil	33	RJ	3302601	Mangaratiba
Brazil	33	RJ	3302700	Maricá
Brazil	33	RJ	3302809	Mendes
Brazil	33	RJ	3302858	Mesquita
Brazil	33	RJ	3302908	Miguel Pereira
Brazil	33	RJ	3303005	Miracema
Brazil	33	RJ	3303104	Natividade
Brazil	33	RJ	3303203	Nilópolis
Brazil	33	RJ	3303302	Niterói
Brazil	33	RJ	3303401	Nova Friburgo
Brazil	33	RJ	3303500	Nova Iguaçu
Brazil	33	RJ	3303609	Paracambi
Brazil	33	RJ	3303708	Paraíba do Sul
Brazil	33	RJ	3303807	Parati
Brazil	33	RJ	3303856	Paty do Alferes
Brazil	33	RJ	3303906	Petrópolis
Brazil	33	RJ	3303955	Pinheiral
Brazil	33	RJ	3304003	Piraí
Brazil	33	RJ	3304102	Porciúncula
Brazil	33	RJ	3304110	Porto Real
Brazil	33	RJ	3304128	Quatis
Brazil	33	RJ	3304144	Queimados
Brazil	33	RJ	3304151	Quissamã
Brazil	33	RJ	3304201	Resende
Brazil	33	RJ	3304300	Rio Bonito
Brazil	33	RJ	3304409	Rio Claro
Brazil	33	RJ	3304508	Rio das Flores
Brazil	33	RJ	3304524	Rio das Ostras
Brazil	33	RJ	3304557	Rio de Janeiro
Brazil	33	RJ	3304607	Santa Maria Madalena
Brazil	33	RJ	3304706	Santo Antônio de Pádua
Brazil	33	RJ	3304805	São Fidélis
Brazil	33	RJ	3304755	São Francisco de Itabapoana
Brazil	33	RJ	3304904	São Gonçalo
Brazil	33	RJ	3305000	São João da Barra
Brazil	33	RJ	3305109	São João de Meriti
Brazil	33	RJ	3305133	São José de Ubá
Brazil	33	RJ	3305158	São José do Vale do Rio Preto
Brazil	33	RJ	3305208	São Pedro da Aldeia
Brazil	33	RJ	3305307	São Sebastião do Alto
Brazil	33	RJ	3305406	Sapucaia
Brazil	33	RJ	3305505	Saquarema
Brazil	33	RJ	3305554	Seropédica
Brazil	33	RJ	3305604	Silva Jardim
Brazil	33	RJ	3305703	Sumidouro
Brazil	33	RJ	3305752	Tanguá
Brazil	33	RJ	3305802	Teresópolis
Brazil	33	RJ	3305901	Trajano de Morais
Brazil	33	RJ	3306008	Três Rios
Brazil	33	RJ	3306107	Valença
Brazil	33	RJ	3306156	Varre-Sai
Brazil	33	RJ	3306206	Vassouras
Brazil	33	RJ	3306305	Volta Redonda
Brazil	27	AL	2700102	Água Branca
Brazil	27	AL	2700201	Anadia
Brazil	27	AL	2700300	Arapiraca
Brazil	27	AL	2700409	Atalaia
Brazil	27	AL	2700508	Barra de Santo Antônio
Brazil	27	AL	2700607	Barra de São Miguel
Brazil	27	AL	2700706	Batalha
Brazil	27	AL	2700805	Belém
Brazil	27	AL	2700904	Belo Monte
Brazil	27	AL	2701001	Boca da Mata
Brazil	27	AL	2701100	Branquinha
Brazil	27	AL	2701209	Cacimbinhas
Brazil	27	AL	2701308	Cajueiro
Brazil	27	AL	2701357	Campestre
Brazil	27	AL	2701407	Campo Alegre
Brazil	27	AL	2701506	Campo Grande
Brazil	27	AL	2701605	Canapi
Brazil	27	AL	2701704	Capela
Brazil	27	AL	2701803	Carneiros
Brazil	27	AL	2701902	Chã Preta
Brazil	27	AL	2702009	Coité do Nóia
Brazil	27	AL	2702108	Colônia Leopoldina
Brazil	27	AL	2702207	Coqueiro Seco
Brazil	27	AL	2702306	Coruripe
Brazil	27	AL	2702355	Craíbas
Brazil	27	AL	2702405	Delmiro Gouveia
Brazil	27	AL	2702504	Dois Riachos
Brazil	27	AL	2702553	Estrela de Alagoas
Brazil	27	AL	2702603	Feira Grande
Brazil	27	AL	2702702	Feliz Deserto
Brazil	27	AL	2702801	Flexeiras
Brazil	27	AL	2702900	Girau do Ponciano
Brazil	27	AL	2703007	Ibateguara
Brazil	27	AL	2703106	Igaci
Brazil	27	AL	2703205	Igreja Nova
Brazil	27	AL	2703304	Inhapi
Brazil	27	AL	2703403	Jacaré dos Homens
Brazil	27	AL	2703502	Jacuípe
Brazil	27	AL	2703601	Japaratinga
Brazil	27	AL	2703700	Jaramataia
Brazil	27	AL	2703759	Jequiá da Praia
Brazil	27	AL	2703809	Joaquim Gomes
Brazil	27	AL	2703908	Jundiá
Brazil	27	AL	2704005	Junqueiro
Brazil	27	AL	2704104	Lagoa da Canoa
Brazil	27	AL	2704203	Limoeiro de Anadia
Brazil	27	AL	2704302	Maceió
Brazil	27	AL	2704401	Major Isidoro
Brazil	27	AL	2704906	Mar Vermelho
Brazil	27	AL	2704500	Maragogi
Brazil	27	AL	2704609	Maravilha
Brazil	27	AL	2704708	Marechal Deodoro
Brazil	27	AL	2704807	Maribondo
Brazil	27	AL	2705002	Mata Grande
Brazil	27	AL	2705101	Matriz de Camaragibe
Brazil	27	AL	2705200	Messias
Brazil	27	AL	2705309	Minador do Negrão
Brazil	27	AL	2705408	Monteirópolis
Brazil	27	AL	2705507	Murici
Brazil	27	AL	2705606	Novo Lino
Brazil	27	AL	2705705	Olho d'Água das Flores
Brazil	27	AL	2705804	Olho d'Água do Casado
Brazil	27	AL	2705903	Olho d'Água Grande
Brazil	27	AL	2706000	Olivença
Brazil	27	AL	2706109	Ouro Branco
Brazil	27	AL	2706208	Palestina
Brazil	27	AL	2706307	Palmeira dos Índios
Brazil	27	AL	2706406	Pão de Açúcar
Brazil	27	AL	2706422	Pariconha
Brazil	27	AL	2706448	Paripueira
Brazil	27	AL	2706505	Passo de Camaragibe
Brazil	27	AL	2706604	Paulo Jacinto
Brazil	27	AL	2706703	Penedo
Brazil	27	AL	2706802	Piaçabuçu
Brazil	27	AL	2706901	Pilar
Brazil	27	AL	2707008	Pindoba
Brazil	27	AL	2707107	Piranhas
Brazil	27	AL	2707206	Poço das Trincheiras
Brazil	27	AL	2707305	Porto Calvo
Brazil	27	AL	2707404	Porto de Pedras
Brazil	27	AL	2707503	Porto Real do Colégio
Brazil	27	AL	2707602	Quebrangulo
Brazil	27	AL	2707701	Rio Largo
Brazil	27	AL	2707800	Roteiro
Brazil	27	AL	2707909	Santa Luzia do Norte
Brazil	27	AL	2708006	Santana do Ipanema
Brazil	27	AL	2708105	Santana do Mundaú
Brazil	27	AL	2708204	São Brás
Brazil	27	AL	2708303	São José da Laje
Brazil	27	AL	2708402	São José da Tapera
Brazil	27	AL	2708501	São Luís do Quitunde
Brazil	27	AL	2708600	São Miguel dos Campos
Brazil	27	AL	2708709	São Miguel dos Milagres
Brazil	27	AL	2708808	São Sebastião
Brazil	27	AL	2708907	Satuba
Brazil	27	AL	2708956	Senador Rui Palmeira
Brazil	27	AL	2709004	Tanque d'Arca
Brazil	27	AL	2709103	Taquarana
Brazil	27	AL	2709152	Teotônio Vilela
Brazil	27	AL	2709202	Traipu
Brazil	27	AL	2709301	União dos Palmares
Brazil	27	AL	2709400	Viçosa
Brazil	17	TO	1700251	Abreulândia
Brazil	17	TO	1700301	Aguiarnópolis
Brazil	17	TO	1700350	Aliança do Tocantins
Brazil	17	TO	1700400	Almas
Brazil	17	TO	1700707	Alvorada
Brazil	17	TO	1701002	Ananás
Brazil	17	TO	1701051	Angico
Brazil	17	TO	1701101	Aparecida do Rio Negro
Brazil	17	TO	1701309	Aragominas
Brazil	17	TO	1701903	Araguacema
Brazil	17	TO	1702000	Araguaçu
Brazil	17	TO	1702109	Araguaína
Brazil	17	TO	1702158	Araguanã
Brazil	17	TO	1702208	Araguatins
Brazil	17	TO	1702307	Arapoema
Brazil	17	TO	1702406	Arraias
Brazil	17	TO	1702554	Augustinópolis
Brazil	17	TO	1702703	Aurora do Tocantins
Brazil	17	TO	1702901	Axixá do Tocantins
Brazil	17	TO	1703008	Babaçulândia
Brazil	17	TO	1703057	Bandeirantes do Tocantins
Brazil	17	TO	1703073	Barra do Ouro
Brazil	17	TO	1703107	Barrolândia
Brazil	17	TO	1703206	Bernardo Sayão
Brazil	17	TO	1703305	Bom Jesus do Tocantins
Brazil	17	TO	1703602	Brasilândia do Tocantins
Brazil	17	TO	1703701	Brejinho de Nazaré
Brazil	17	TO	1703800	Buriti do Tocantins
Brazil	17	TO	1703826	Cachoeirinha
Brazil	17	TO	1703842	Campos Lindos
Brazil	17	TO	1703867	Cariri do Tocantins
Brazil	17	TO	1703883	Carmolândia
Brazil	17	TO	1703891	Carrasco Bonito
Brazil	17	TO	1703909	Caseara
Brazil	17	TO	1704105	Centenário
Brazil	17	TO	1705102	Chapada da Natividade
Brazil	17	TO	1704600	Chapada de Areia
Brazil	17	TO	1705508	Colinas do Tocantins
Brazil	17	TO	1716703	Colméia
Brazil	17	TO	1705557	Combinado
Brazil	17	TO	1705607	Conceição do Tocantins
Brazil	17	TO	1706001	Couto de Magalhães
Brazil	17	TO	1706100	Cristalândia
Brazil	17	TO	1706258	Crixás do Tocantins
Brazil	17	TO	1706506	Darcinópolis
Brazil	17	TO	1707009	Dianópolis
Brazil	17	TO	1707108	Divinópolis do Tocantins
Brazil	17	TO	1707207	Dois Irmãos do Tocantins
Brazil	17	TO	1707306	Dueré
Brazil	17	TO	1707405	Esperantina
Brazil	17	TO	1707553	Fátima
Brazil	17	TO	1707652	Figueirópolis
Brazil	17	TO	1707702	Filadélfia
Brazil	17	TO	1708205	Formoso do Araguaia
Brazil	17	TO	1708254	Fortaleza do Tabocão
Brazil	17	TO	1708304	Goianorte
Brazil	17	TO	1709005	Goiatins
Brazil	17	TO	1709302	Guaraí
Brazil	17	TO	1709500	Gurupi
Brazil	17	TO	1709807	Ipueiras
Brazil	17	TO	1710508	Itacajá
Brazil	17	TO	1710706	Itaguatins
Brazil	17	TO	1710904	Itapiratins
Brazil	17	TO	1711100	Itaporã do Tocantins
Brazil	17	TO	1711506	Jaú do Tocantins
Brazil	17	TO	1711803	Juarina
Brazil	17	TO	1711902	Lagoa da Confusão
Brazil	17	TO	1711951	Lagoa do Tocantins
Brazil	17	TO	1712009	Lajeado
Brazil	17	TO	1712157	Lavandeira
Brazil	17	TO	1712405	Lizarda
Brazil	17	TO	1712454	Luzinópolis
Brazil	17	TO	1712504	Marianópolis do Tocantins
Brazil	17	TO	1712702	Mateiros
Brazil	17	TO	1712801	Maurilândia do Tocantins
Brazil	17	TO	1713205	Miracema do Tocantins
Brazil	17	TO	1713304	Miranorte
Brazil	17	TO	1713601	Monte do Carmo
Brazil	17	TO	1713700	Monte Santo do Tocantins
Brazil	17	TO	1713957	Muricilândia
Brazil	17	TO	1714203	Natividade
Brazil	17	TO	1714302	Nazaré
Brazil	17	TO	1714880	Nova Olinda
Brazil	17	TO	1715002	Nova Rosalândia
Brazil	17	TO	1715101	Novo Acordo
Brazil	17	TO	1715150	Novo Alegre
Brazil	17	TO	1715259	Novo Jardim
Brazil	17	TO	1715507	Oliveira de Fátima
Brazil	17	TO	1721000	Palmas
Brazil	17	TO	1715705	Palmeirante
Brazil	17	TO	1713809	Palmeiras do Tocantins
Brazil	17	TO	1715754	Palmeirópolis
Brazil	17	TO	1716109	Paraíso do Tocantins
Brazil	17	TO	1716208	Paranã
Brazil	17	TO	1716307	Pau D'Arco
Brazil	17	TO	1716505	Pedro Afonso
Brazil	17	TO	1716604	Peixe
Brazil	17	TO	1716653	Pequizeiro
Brazil	17	TO	1717008	Pindorama do Tocantins
Brazil	17	TO	1717206	Piraquê
Brazil	17	TO	1717503	Pium
Brazil	17	TO	1717800	Ponte Alta do Bom Jesus
Brazil	17	TO	1717909	Ponte Alta do Tocantins
Brazil	17	TO	1718006	Porto Alegre do Tocantins
Brazil	17	TO	1718204	Porto Nacional
Brazil	17	TO	1718303	Praia Norte
Brazil	17	TO	1718402	Presidente Kennedy
Brazil	17	TO	1718451	Pugmil
Brazil	17	TO	1718501	Recursolândia
Brazil	17	TO	1718550	Riachinho
Brazil	17	TO	1718659	Rio da Conceição
Brazil	17	TO	1718709	Rio dos Bois
Brazil	17	TO	1718758	Rio Sono
Brazil	17	TO	1718808	Sampaio
Brazil	17	TO	1718840	Sandolândia
Brazil	17	TO	1718865	Santa Fé do Araguaia
Brazil	17	TO	1718881	Santa Maria do Tocantins
Brazil	17	TO	1718899	Santa Rita do Tocantins
Brazil	17	TO	1718907	Santa Rosa do Tocantins
Brazil	17	TO	1719004	Santa Tereza do Tocantins
Brazil	17	TO	1720002	Santa Terezinha do Tocantins
Brazil	17	TO	1720101	São Bento do Tocantins
Brazil	17	TO	1720150	São Félix do Tocantins
Brazil	17	TO	1720200	São Miguel do Tocantins
Brazil	17	TO	1720259	São Salvador do Tocantins
Brazil	17	TO	1720309	São Sebastião do Tocantins
Brazil	17	TO	1720499	São Valério da Natividade
Brazil	17	TO	1720655	Silvanópolis
Brazil	17	TO	1720804	Sítio Novo do Tocantins
Brazil	17	TO	1720853	Sucupira
Brazil	17	TO	1720903	Taguatinga
Brazil	17	TO	1720937	Taipas do Tocantins
Brazil	17	TO	1720978	Talismã
Brazil	17	TO	1721109	Tocantínia
Brazil	17	TO	1721208	Tocantinópolis
Brazil	17	TO	1721257	Tupirama
Brazil	17	TO	1721307	Tupiratins
Brazil	17	TO	1722081	Wanderlândia
Brazil	17	TO	1722107	Xambioá
Brazil	51	MT	5100102	Acorizal
Brazil	51	MT	5100201	Água Boa
Brazil	51	MT	5100250	Alta Floresta
Brazil	51	MT	5100300	Alto Araguaia
Brazil	51	MT	5100359	Alto Boa Vista
Brazil	51	MT	5100409	Alto Garças
Brazil	51	MT	5100508	Alto Paraguai
Brazil	51	MT	5100607	Alto Taquari
Brazil	51	MT	5100805	Apiacás
Brazil	51	MT	5101001	Araguaiana
Brazil	51	MT	5101209	Araguainha
Brazil	51	MT	5101258	Araputanga
Brazil	51	MT	5101308	Arenápolis
Brazil	51	MT	5101407	Aripuanã
Brazil	51	MT	5101605	Barão de Melgaço
Brazil	51	MT	5101704	Barra do Bugres
Brazil	51	MT	5101803	Barra do Garças
Brazil	51	MT	5101852	Bom Jesus do Araguaia
Brazil	51	MT	5101902	Brasnorte
Brazil	51	MT	5102504	Cáceres
Brazil	51	MT	5102603	Campinápolis
Brazil	51	MT	5102637	Campo Novo do Parecis
Brazil	51	MT	5102678	Campo Verde
Brazil	51	MT	5102686	Campos de Júlio
Brazil	51	MT	5102694	Canabrava do Norte
Brazil	51	MT	5102702	Canarana
Brazil	51	MT	5102793	Carlinda
Brazil	51	MT	5102850	Castanheira
Brazil	51	MT	5103007	Chapada dos Guimarães
Brazil	51	MT	5103056	Cláudia
Brazil	51	MT	5103106	Cocalinho
Brazil	51	MT	5103205	Colíder
Brazil	51	MT	5103254	Colniza
Brazil	51	MT	5103304	Comodoro
Brazil	51	MT	5103353	Confresa
Brazil	51	MT	5103361	Conquista D'Oeste
Brazil	51	MT	5103379	Cotriguaçu
Brazil	51	MT	5103403	Cuiabá
Brazil	51	MT	5103437	Curvelândia
Brazil	51	MT	5103452	Denise
Brazil	51	MT	5103502	Diamantino
Brazil	51	MT	5103601	Dom Aquino
Brazil	51	MT	5103700	Feliz Natal
Brazil	51	MT	5103809	Figueirópolis D'Oeste
Brazil	51	MT	5103858	Gaúcha do Norte
Brazil	51	MT	5103908	General Carneiro
Brazil	51	MT	5103957	Glória D'Oeste
Brazil	51	MT	5104104	Guarantã do Norte
Brazil	51	MT	5104203	Guiratinga
Brazil	51	MT	5104500	Indiavaí
Brazil	51	MT	5104526	Ipiranga do Norte
Brazil	51	MT	5104542	Itanhangá
Brazil	51	MT	5104559	Itaúba
Brazil	51	MT	5104609	Itiquira
Brazil	51	MT	5104807	Jaciara
Brazil	51	MT	5104906	Jangada
Brazil	51	MT	5105002	Jauru
Brazil	51	MT	5105101	Juara
Brazil	51	MT	5105150	Juína
Brazil	51	MT	5105176	Juruena
Brazil	51	MT	5105200	Juscimeira
Brazil	51	MT	5105234	Lambari D'Oeste
Brazil	51	MT	5105259	Lucas do Rio Verde
Brazil	51	MT	5105309	Luciára
Brazil	51	MT	5105580	Marcelândia
Brazil	51	MT	5105606	Matupá
Brazil	51	MT	5105622	Mirassol d'Oeste
Brazil	51	MT	5105903	Nobres
Brazil	51	MT	5106000	Nortelândia
Brazil	51	MT	5106109	Nossa Senhora do Livramento
Brazil	51	MT	5106158	Nova Bandeirantes
Brazil	51	MT	5106208	Nova Brasilândia
Brazil	51	MT	5106216	Nova Canaã do Norte
Brazil	51	MT	5108808	Nova Guarita
Brazil	51	MT	5106182	Nova Lacerda
Brazil	51	MT	5108857	Nova Marilândia
Brazil	51	MT	5108907	Nova Maringá
Brazil	51	MT	5108956	Nova Monte Verde
Brazil	51	MT	5106224	Nova Mutum
Brazil	51	MT	5106174	Nova Nazaré
Brazil	51	MT	5106232	Nova Olímpia
Brazil	51	MT	5106190	Nova Santa Helena
Brazil	51	MT	5106240	Nova Ubiratã
Brazil	51	MT	5106257	Nova Xavantina
Brazil	51	MT	5106273	Novo Horizonte do Norte
Brazil	51	MT	5106265	Novo Mundo
Brazil	51	MT	5106315	Novo Santo Antônio
Brazil	51	MT	5106281	Novo São Joaquim
Brazil	51	MT	5106299	Paranaíta
Brazil	51	MT	5106307	Paranatinga
Brazil	51	MT	5106372	Pedra Preta
Brazil	51	MT	5106422	Peixoto de Azevedo
Brazil	51	MT	5106455	Planalto da Serra
Brazil	51	MT	5106505	Poconé
Brazil	51	MT	5106653	Pontal do Araguaia
Brazil	51	MT	5106703	Ponte Branca
Brazil	51	MT	5106752	Pontes e Lacerda
Brazil	51	MT	5106778	Porto Alegre do Norte
Brazil	51	MT	5106802	Porto dos Gaúchos
Brazil	51	MT	5106828	Porto Esperidião
Brazil	51	MT	5106851	Porto Estrela
Brazil	51	MT	5107008	Poxoréo
Brazil	51	MT	5107040	Primavera do Leste
Brazil	51	MT	5107065	Querência
Brazil	51	MT	5107156	Reserva do Cabaçal
Brazil	51	MT	5107180	Ribeirão Cascalheira
Brazil	51	MT	5107198	Ribeirãozinho
Brazil	51	MT	5107206	Rio Branco
Brazil	51	MT	5107578	Rondolândia
Brazil	51	MT	5107602	Rondonópolis
Brazil	51	MT	5107701	Rosário Oeste
Brazil	51	MT	5107750	Salto do Céu
Brazil	51	MT	5107248	Santa Carmem
Brazil	51	MT	5107743	Santa Cruz do Xingu
Brazil	51	MT	5107768	Santa Rita do Trivelato
Brazil	51	MT	5107776	Santa Terezinha
Brazil	51	MT	5107263	Santo Afonso
Brazil	51	MT	5107792	Santo Antônio do Leste
Brazil	51	MT	5107800	Santo Antônio do Leverger
Brazil	51	MT	5107859	São Félix do Araguaia
Brazil	51	MT	5107297	São José do Povo
Brazil	51	MT	5107305	São José do Rio Claro
Brazil	51	MT	5107354	São José do Xingu
Brazil	51	MT	5107107	São José dos Quatro Marcos
Brazil	51	MT	5107404	São Pedro da Cipa
Brazil	51	MT	5107875	Sapezal
Brazil	51	MT	5107883	Serra Nova Dourada
Brazil	51	MT	5107909	Sinop
Brazil	51	MT	5107925	Sorriso
Brazil	51	MT	5107941	Tabaporã
Brazil	51	MT	5107958	Tangará da Serra
Brazil	51	MT	5108006	Tapurah
Brazil	51	MT	5108055	Terra Nova do Norte
Brazil	51	MT	5108105	Tesouro
Brazil	51	MT	5108204	Torixoréu
Brazil	51	MT	5108303	União do Sul
Brazil	51	MT	5108352	Vale de São Domingos
Brazil	51	MT	5108402	Várzea Grande
Brazil	51	MT	5108501	Vera
Brazil	51	MT	5105507	Vila Bela da Santíssima Trindade
Brazil	51	MT	5108600	Vila Rica
Brazil	15	PA	1500107	Abaetetuba
Brazil	15	PA	1500131	Abel Figueiredo
Brazil	15	PA	1500206	Acará
Brazil	15	PA	1500305	Afuá
Brazil	15	PA	1500347	Água Azul do Norte
Brazil	15	PA	1500404	Alenquer
Brazil	15	PA	1500503	Almeirim
Brazil	15	PA	1500602	Altamira
Brazil	15	PA	1500701	Anajás
Brazil	15	PA	1500800	Ananindeua
Brazil	15	PA	1500859	Anapu
Brazil	15	PA	1500909	Augusto Corrêa
Brazil	15	PA	1500958	Aurora do Pará
Brazil	15	PA	1501006	Aveiro
Brazil	15	PA	1501105	Bagre
Brazil	15	PA	1501204	Baião
Brazil	15	PA	1501253	Bannach
Brazil	15	PA	1501303	Barcarena
Brazil	15	PA	1501402	Belém
Brazil	15	PA	1501451	Belterra
Brazil	15	PA	1501501	Benevides
Brazil	15	PA	1501576	Bom Jesus do Tocantins
Brazil	15	PA	1501600	Bonito
Brazil	15	PA	1501709	Bragança
Brazil	15	PA	1501725	Brasil Novo
Brazil	15	PA	1501758	Brejo Grande do Araguaia
Brazil	15	PA	1501782	Breu Branco
Brazil	15	PA	1501808	Breves
Brazil	15	PA	1501907	Bujaru
Brazil	15	PA	1502004	Cachoeira do Arari
Brazil	15	PA	1501956	Cachoeira do Piriá
Brazil	15	PA	1502103	Cametá
Brazil	15	PA	1502152	Canaã dos Carajás
Brazil	15	PA	1502202	Capanema
Brazil	15	PA	1502301	Capitão Poço
Brazil	15	PA	1502400	Castanhal
Brazil	15	PA	1502509	Chaves
Brazil	15	PA	1502608	Colares
Brazil	15	PA	1502707	Conceição do Araguaia
Brazil	15	PA	1502756	Concórdia do Pará
Brazil	15	PA	1502764	Cumaru do Norte
Brazil	15	PA	1502772	Curionópolis
Brazil	15	PA	1502806	Curralinho
Brazil	15	PA	1502855	Curuá
Brazil	15	PA	1502905	Curuçá
Brazil	15	PA	1502939	Dom Eliseu
Brazil	15	PA	1502954	Eldorado dos Carajás
Brazil	15	PA	1503002	Faro
Brazil	15	PA	1503044	Floresta do Araguaia
Brazil	15	PA	1503077	Garrafão do Norte
Brazil	15	PA	1503093	Goianésia do Pará
Brazil	15	PA	1503101	Gurupá
Brazil	15	PA	1503200	Igarapé-Açu
Brazil	15	PA	1503309	Igarapé-Miri
Brazil	15	PA	1503408	Inhangapi
Brazil	15	PA	1503457	Ipixuna do Pará
Brazil	15	PA	1503507	Irituia
Brazil	15	PA	1503606	Itaituba
Brazil	15	PA	1503705	Itupiranga
Brazil	15	PA	1503754	Jacareacanga
Brazil	15	PA	1503804	Jacundá
Brazil	15	PA	1503903	Juruti
Brazil	15	PA	1504000	Limoeiro do Ajuru
Brazil	15	PA	1504059	Mãe do Rio
Brazil	15	PA	1504109	Magalhães Barata
Brazil	15	PA	1504208	Marabá
Brazil	15	PA	1504307	Maracanã
Brazil	15	PA	1504406	Marapanim
Brazil	15	PA	1504422	Marituba
Brazil	15	PA	1504455	Medicilândia
Brazil	15	PA	1504505	Melgaço
Brazil	15	PA	1504604	Mocajuba
Brazil	15	PA	1504703	Moju
Brazil	15	PA	1504802	Monte Alegre
Brazil	15	PA	1504901	Muaná
Brazil	15	PA	1504950	Nova Esperança do Piriá
Brazil	15	PA	1504976	Nova Ipixuna
Brazil	15	PA	1505007	Nova Timboteua
Brazil	15	PA	1505031	Novo Progresso
Brazil	15	PA	1505064	Novo Repartimento
Brazil	15	PA	1505106	Óbidos
Brazil	15	PA	1505205	Oeiras do Pará
Brazil	15	PA	1505304	Oriximiná
Brazil	15	PA	1505403	Ourém
Brazil	15	PA	1505437	Ourilândia do Norte
Brazil	15	PA	1505486	Pacajá
Brazil	15	PA	1505494	Palestina do Pará
Brazil	15	PA	1505502	Paragominas
Brazil	15	PA	1505536	Parauapebas
Brazil	15	PA	1505551	Pau D'Arco
Brazil	15	PA	1505601	Peixe-Boi
Brazil	15	PA	1505635	Piçarra
Brazil	15	PA	1505650	Placas
Brazil	15	PA	1505700	Ponta de Pedras
Brazil	15	PA	1505809	Portel
Brazil	15	PA	1505908	Porto de Moz
Brazil	15	PA	1506005	Prainha
Brazil	15	PA	1506104	Primavera
Brazil	15	PA	1506112	Quatipuru
Brazil	15	PA	1506138	Redenção
Brazil	15	PA	1506161	Rio Maria
Brazil	15	PA	1506187	Rondon do Pará
Brazil	15	PA	1506195	Rurópolis
Brazil	15	PA	1506203	Salinópolis
Brazil	15	PA	1506302	Salvaterra
Brazil	15	PA	1506351	Santa Bárbara do Pará
Brazil	15	PA	1506401	Santa Cruz do Arari
Brazil	15	PA	1506500	Santa Isabel do Pará
Brazil	15	PA	1506559	Santa Luzia do Pará
Brazil	15	PA	1506583	Santa Maria das Barreiras
Brazil	15	PA	1506609	Santa Maria do Pará
Brazil	15	PA	1506708	Santana do Araguaia
Brazil	15	PA	1506807	Santarém
Brazil	15	PA	1506906	Santarém Novo
Brazil	15	PA	1507003	Santo Antônio do Tauá
Brazil	15	PA	1507102	São Caetano de Odivelas
Brazil	15	PA	1507151	São Domingos do Araguaia
Brazil	15	PA	1507201	São Domingos do Capim
Brazil	15	PA	1507300	São Félix do Xingu
Brazil	15	PA	1507409	São Francisco do Pará
Brazil	15	PA	1507458	São Geraldo do Araguaia
Brazil	15	PA	1507466	São João da Ponta
Brazil	15	PA	1507474	São João de Pirabas
Brazil	15	PA	1507508	São João do Araguaia
Brazil	15	PA	1507607	São Miguel do Guamá
Brazil	15	PA	1507706	São Sebastião da Boa Vista
Brazil	15	PA	1507755	Sapucaia
Brazil	15	PA	1507805	Senador José Porfírio
Brazil	15	PA	1507904	Soure
Brazil	15	PA	1507953	Tailândia
Brazil	15	PA	1507961	Terra Alta
Brazil	15	PA	1507979	Terra Santa
Brazil	15	PA	1508001	Tomé-Açu
Brazil	15	PA	1508035	Tracuateua
Brazil	15	PA	1508050	Trairão
Brazil	15	PA	1508084	Tucumã
Brazil	15	PA	1508100	Tucuruí
Brazil	15	PA	1508126	Ulianópolis
Brazil	15	PA	1508159	Uruará
Brazil	15	PA	1508209	Vigia
Brazil	15	PA	1508308	Viseu
Brazil	15	PA	1508357	Vitória do Xingu
Brazil	15	PA	1508407	Xinguara
Brazil	24	RN	2400109	Acari
Brazil	24	RN	2400208	Açu
Brazil	24	RN	2400307	Afonso Bezerra
Brazil	24	RN	2400406	Água Nova
Brazil	24	RN	2400505	Alexandria
Brazil	24	RN	2400604	Almino Afonso
Brazil	24	RN	2400703	Alto do Rodrigues
Brazil	24	RN	2400802	Angicos
Brazil	24	RN	2400901	Antônio Martins
Brazil	24	RN	2401008	Apodi
Brazil	24	RN	2401107	Areia Branca
Brazil	24	RN	2401206	Arês
Brazil	24	RN	2401305	Augusto Severo
Brazil	24	RN	2401404	Baía Formosa
Brazil	24	RN	2401453	Baraúna
Brazil	24	RN	2401503	Barcelona
Brazil	24	RN	2401602	Bento Fernandes
Brazil	24	RN	2401651	Bodó
Brazil	24	RN	2401701	Bom Jesus
Brazil	24	RN	2401800	Brejinho
Brazil	24	RN	2401859	Caiçara do Norte
Brazil	24	RN	2401909	Caiçara do Rio do Vento
Brazil	24	RN	2402006	Caicó
Brazil	24	RN	2402105	Campo Redondo
Brazil	24	RN	2402204	Canguaretama
Brazil	24	RN	2402303	Caraúbas
Brazil	24	RN	2402402	Carnaúba dos Dantas
Brazil	24	RN	2402501	Carnaubais
Brazil	24	RN	2402600	Ceará-Mirim
Brazil	24	RN	2402709	Cerro Corá
Brazil	24	RN	2402808	Coronel Ezequiel
Brazil	24	RN	2402907	Coronel João Pessoa
Brazil	24	RN	2403004	Cruzeta
Brazil	24	RN	2403103	Currais Novos
Brazil	24	RN	2403202	Doutor Severiano
Brazil	24	RN	2403301	Encanto
Brazil	24	RN	2403400	Equador
Brazil	24	RN	2403509	Espírito Santo
Brazil	24	RN	2403608	Extremoz
Brazil	24	RN	2403707	Felipe Guerra
Brazil	24	RN	2403756	Fernando Pedroza
Brazil	24	RN	2403806	Florânia
Brazil	24	RN	2403905	Francisco Dantas
Brazil	24	RN	2404002	Frutuoso Gomes
Brazil	24	RN	2404101	Galinhos
Brazil	24	RN	2404200	Goianinha
Brazil	24	RN	2404309	Governador Dix-Sept Rosado
Brazil	24	RN	2404408	Grossos
Brazil	24	RN	2404507	Guamaré
Brazil	24	RN	2404606	Ielmo Marinho
Brazil	24	RN	2404705	Ipanguaçu
Brazil	24	RN	2404804	Ipueira
Brazil	24	RN	2404853	Itajá
Brazil	24	RN	2404903	Itaú
Brazil	24	RN	2405009	Jaçanã
Brazil	24	RN	2405108	Jandaíra
Brazil	24	RN	2405207	Janduís
Brazil	24	RN	2405306	Januário Cicco
Brazil	24	RN	2405405	Japi
Brazil	24	RN	2405504	Jardim de Angicos
Brazil	24	RN	2405603	Jardim de Piranhas
Brazil	24	RN	2405702	Jardim do Seridó
Brazil	24	RN	2405801	João Câmara
Brazil	24	RN	2405900	João Dias
Brazil	24	RN	2406007	José da Penha
Brazil	24	RN	2406106	Jucurutu
Brazil	24	RN	2406155	Jundiá
Brazil	24	RN	2406205	Lagoa d'Anta
Brazil	24	RN	2406304	Lagoa de Pedras
Brazil	24	RN	2406403	Lagoa de Velhos
Brazil	24	RN	2406502	Lagoa Nova
Brazil	24	RN	2406601	Lagoa Salgada
Brazil	24	RN	2406700	Lajes
Brazil	24	RN	2406809	Lajes Pintadas
Brazil	24	RN	2406908	Lucrécia
Brazil	24	RN	2407005	Luís Gomes
Brazil	24	RN	2407104	Macaíba
Brazil	24	RN	2407203	Macau
Brazil	24	RN	2407252	Major Sales
Brazil	24	RN	2407302	Marcelino Vieira
Brazil	24	RN	2407401	Martins
Brazil	24	RN	2407500	Maxaranguape
Brazil	24	RN	2407609	Messias Targino
Brazil	24	RN	2407708	Montanhas
Brazil	24	RN	2407807	Monte Alegre
Brazil	24	RN	2407906	Monte das Gameleiras
Brazil	24	RN	2408003	Mossoró
Brazil	24	RN	2408102	Natal
Brazil	24	RN	2408201	Nísia Floresta
Brazil	24	RN	2408300	Nova Cruz
Brazil	24	RN	2408409	Olho-d'Água do Borges
Brazil	24	RN	2408508	Ouro Branco
Brazil	24	RN	2408607	Paraná
Brazil	24	RN	2408706	Paraú
Brazil	24	RN	2408805	Parazinho
Brazil	24	RN	2408904	Parelhas
Brazil	24	RN	2403251	Parnamirim
Brazil	24	RN	2409100	Passa e Fica
Brazil	24	RN	2409209	Passagem
Brazil	24	RN	2409308	Patu
Brazil	24	RN	2409407	Pau dos Ferros
Brazil	24	RN	2409506	Pedra Grande
Brazil	24	RN	2409605	Pedra Preta
Brazil	24	RN	2409704	Pedro Avelino
Brazil	24	RN	2409803	Pedro Velho
Brazil	24	RN	2409902	Pendências
Brazil	24	RN	2410009	Pilões
Brazil	24	RN	2410108	Poço Branco
Brazil	24	RN	2410207	Portalegre
Brazil	24	RN	2410256	Porto do Mangue
Brazil	24	RN	2410306	Presidente Juscelino
Brazil	24	RN	2410405	Pureza
Brazil	24	RN	2410504	Rafael Fernandes
Brazil	24	RN	2410603	Rafael Godeiro
Brazil	24	RN	2410702	Riacho da Cruz
Brazil	24	RN	2410801	Riacho de Santana
Brazil	24	RN	2410900	Riachuelo
Brazil	24	RN	2408953	Rio do Fogo
Brazil	24	RN	2411007	Rodolfo Fernandes
Brazil	24	RN	2411106	Ruy Barbosa
Brazil	24	RN	2411205	Santa Cruz
Brazil	24	RN	2409332	Santa Maria
Brazil	24	RN	2411403	Santana do Matos
Brazil	24	RN	2411429	Santana do Seridó
Brazil	24	RN	2411502	Santo Antônio
Brazil	24	RN	2411601	São Bento do Norte
Brazil	24	RN	2411700	São Bento do Trairí
Brazil	24	RN	2411809	São Fernando
Brazil	24	RN	2411908	São Francisco do Oeste
Brazil	24	RN	2412005	São Gonçalo do Amarante
Brazil	24	RN	2412104	São João do Sabugi
Brazil	24	RN	2412203	São José de Mipibu
Brazil	24	RN	2412302	São José do Campestre
Brazil	24	RN	2412401	São José do Seridó
Brazil	24	RN	2412500	São Miguel
Brazil	24	RN	2412559	São Miguel do Gostoso
Brazil	24	RN	2412609	São Paulo do Potengi
Brazil	24	RN	2412708	São Pedro
Brazil	24	RN	2412807	São Rafael
Brazil	24	RN	2412906	São Tomé
Brazil	24	RN	2413003	São Vicente
Brazil	24	RN	2413102	Senador Elói de Souza
Brazil	24	RN	2413201	Senador Georgino Avelino
Brazil	24	RN	2413300	Serra de São Bento
Brazil	24	RN	2413359	Serra do Mel
Brazil	24	RN	2413409	Serra Negra do Norte
Brazil	24	RN	2413508	Serrinha
Brazil	24	RN	2413557	Serrinha dos Pintos
Brazil	24	RN	2413607	Severiano Melo
Brazil	24	RN	2413706	Sítio Novo
Brazil	24	RN	2413805	Taboleiro Grande
Brazil	24	RN	2413904	Taipu
Brazil	24	RN	2414001	Tangará
Brazil	24	RN	2414100	Tenente Ananias
Brazil	24	RN	2414159	Tenente Laurentino Cruz
Brazil	24	RN	2411056	Tibau
Brazil	24	RN	2414209	Tibau do Sul
Brazil	24	RN	2414308	Timbaúba dos Batistas
Brazil	24	RN	2414407	Touros
Brazil	24	RN	2414456	Triunfo Potiguar
Brazil	24	RN	2414506	Umarizal
Brazil	24	RN	2414605	Upanema
Brazil	24	RN	2414704	Várzea
Brazil	24	RN	2414753	Venha-Ver
Brazil	24	RN	2414803	Vera Cruz
Brazil	24	RN	2414902	Viçosa
Brazil	24	RN	2415008	Vila Flor
Brazil	23	CE	2300101	Abaiara
Brazil	23	CE	2300150	Acarape
Brazil	23	CE	2300200	Acaraú
Brazil	23	CE	2300309	Acopiara
Brazil	23	CE	2300408	Aiuaba
Brazil	23	CE	2300507	Alcântaras
Brazil	23	CE	2300606	Altaneira
Brazil	23	CE	2300705	Alto Santo
Brazil	23	CE	2300754	Amontada
Brazil	23	CE	2300804	Antonina do Norte
Brazil	23	CE	2300903	Apuiarés
Brazil	23	CE	2301000	Aquiraz
Brazil	23	CE	2301109	Aracati
Brazil	23	CE	2301208	Aracoiaba
Brazil	23	CE	2301257	Ararendá
Brazil	23	CE	2301307	Araripe
Brazil	23	CE	2301406	Aratuba
Brazil	23	CE	2301505	Arneiroz
Brazil	23	CE	2301604	Assaré
Brazil	23	CE	2301703	Aurora
Brazil	23	CE	2301802	Baixio
Brazil	23	CE	2301851	Banabuiú
Brazil	23	CE	2301901	Barbalha
Brazil	23	CE	2301950	Barreira
Brazil	23	CE	2302008	Barro
Brazil	23	CE	2302057	Barroquinha
Brazil	23	CE	2302107	Baturité
Brazil	23	CE	2302206	Beberibe
Brazil	23	CE	2302305	Bela Cruz
Brazil	23	CE	2302404	Boa Viagem
Brazil	23	CE	2302503	Brejo Santo
Brazil	23	CE	2302602	Camocim
Brazil	23	CE	2302701	Campos Sales
Brazil	23	CE	2302800	Canindé
Brazil	23	CE	2302909	Capistrano
Brazil	23	CE	2303006	Caridade
Brazil	23	CE	2303105	Cariré
Brazil	23	CE	2303204	Caririaçu
Brazil	23	CE	2303303	Cariús
Brazil	23	CE	2303402	Carnaubal
Brazil	23	CE	2303501	Cascavel
Brazil	23	CE	2303600	Catarina
Brazil	23	CE	2303659	Catunda
Brazil	23	CE	2303709	Caucaia
Brazil	23	CE	2303808	Cedro
Brazil	23	CE	2303907	Chaval
Brazil	23	CE	2303931	Choró
Brazil	23	CE	2303956	Chorozinho
Brazil	23	CE	2304004	Coreaú
Brazil	23	CE	2304103	Crateús
Brazil	23	CE	2304202	Crato
Brazil	23	CE	2304236	Croatá
Brazil	23	CE	2304251	Cruz
Brazil	23	CE	2304269	Deputado Irapuan Pinheiro
Brazil	23	CE	2304277	Ererê
Brazil	23	CE	2304285	Eusébio
Brazil	23	CE	2304301	Farias Brito
Brazil	23	CE	2304350	Forquilha
Brazil	23	CE	2304400	Fortaleza
Brazil	23	CE	2304459	Fortim
Brazil	23	CE	2304509	Frecheirinha
Brazil	23	CE	2304608	General Sampaio
Brazil	23	CE	2304657	Graça
Brazil	23	CE	2304707	Granja
Brazil	23	CE	2304806	Granjeiro
Brazil	23	CE	2304905	Groaíras
Brazil	23	CE	2304954	Guaiúba
Brazil	23	CE	2305001	Guaraciaba do Norte
Brazil	23	CE	2305100	Guaramiranga
Brazil	23	CE	2305209	Hidrolândia
Brazil	23	CE	2305233	Horizonte
Brazil	23	CE	2305266	Ibaretama
Brazil	23	CE	2305308	Ibiapina
Brazil	23	CE	2305332	Ibicuitinga
Brazil	23	CE	2305357	Icapuí
Brazil	23	CE	2305407	Icó
Brazil	23	CE	2305506	Iguatu
Brazil	23	CE	2305605	Independência
Brazil	23	CE	2305654	Ipaporanga
Brazil	23	CE	2305704	Ipaumirim
Brazil	23	CE	2305803	Ipu
Brazil	23	CE	2305902	Ipueiras
Brazil	23	CE	2306009	Iracema
Brazil	23	CE	2306108	Irauçuba
Brazil	23	CE	2306207	Itaiçaba
Brazil	23	CE	2306256	Itaitinga
Brazil	23	CE	2306306	Itapagé
Brazil	23	CE	2306405	Itapipoca
Brazil	23	CE	2306504	Itapiúna
Brazil	23	CE	2306553	Itarema
Brazil	23	CE	2306603	Itatira
Brazil	23	CE	2306702	Jaguaretama
Brazil	23	CE	2306801	Jaguaribara
Brazil	23	CE	2306900	Jaguaribe
Brazil	23	CE	2307007	Jaguaruana
Brazil	23	CE	2307106	Jardim
Brazil	23	CE	2307205	Jati
Brazil	23	CE	2307254	Jijoca de Jericoacoara
Brazil	23	CE	2307304	Juazeiro do Norte
Brazil	23	CE	2307403	Jucás
Brazil	23	CE	2307502	Lavras da Mangabeira
Brazil	23	CE	2307601	Limoeiro do Norte
Brazil	23	CE	2307635	Madalena
Brazil	23	CE	2307650	Maracanaú
Brazil	23	CE	2307700	Maranguape
Brazil	23	CE	2307809	Marco
Brazil	23	CE	2307908	Martinópole
Brazil	23	CE	2308005	Massapê
Brazil	23	CE	2308104	Mauriti
Brazil	23	CE	2308203	Meruoca
Brazil	23	CE	2308302	Milagres
Brazil	23	CE	2308351	Milhã
Brazil	23	CE	2308377	Miraíma
Brazil	23	CE	2308401	Missão Velha
Brazil	23	CE	2308500	Mombaça
Brazil	23	CE	2308609	Monsenhor Tabosa
Brazil	23	CE	2308708	Morada Nova
Brazil	23	CE	2308807	Moraújo
Brazil	23	CE	2308906	Morrinhos
Brazil	23	CE	2309003	Mucambo
Brazil	23	CE	2309102	Mulungu
Brazil	23	CE	2309201	Nova Olinda
Brazil	23	CE	2309300	Nova Russas
Brazil	23	CE	2309409	Novo Oriente
Brazil	23	CE	2309458	Ocara
Brazil	23	CE	2309508	Orós
Brazil	23	CE	2309607	Pacajus
Brazil	23	CE	2309706	Pacatuba
Brazil	23	CE	2309805	Pacoti
Brazil	23	CE	2309904	Pacujá
Brazil	23	CE	2310001	Palhano
Brazil	23	CE	2310100	Palmácia
Brazil	23	CE	2310209	Paracuru
Brazil	23	CE	2310258	Paraipaba
Brazil	23	CE	2310308	Parambu
Brazil	23	CE	2310407	Paramoti
Brazil	23	CE	2310506	Pedra Branca
Brazil	23	CE	2310605	Penaforte
Brazil	23	CE	2310704	Pentecoste
Brazil	23	CE	2310803	Pereiro
Brazil	23	CE	2310852	Pindoretama
Brazil	23	CE	2310902	Piquet Carneiro
Brazil	23	CE	2310951	Pires Ferreira
Brazil	23	CE	2311009	Poranga
Brazil	23	CE	2311108	Porteiras
Brazil	23	CE	2311207	Potengi
Brazil	23	CE	2311231	Potiretama
Brazil	23	CE	2311264	Quiterianópolis
Brazil	23	CE	2311306	Quixadá
Brazil	23	CE	2311355	Quixelô
Brazil	23	CE	2311405	Quixeramobim
Brazil	23	CE	2311504	Quixeré
Brazil	23	CE	2311603	Redenção
Brazil	23	CE	2311702	Reriutaba
Brazil	23	CE	2311801	Russas
Brazil	23	CE	2311900	Saboeiro
Brazil	23	CE	2311959	Salitre
Brazil	23	CE	2312205	Santa Quitéria
Brazil	23	CE	2312007	Santana do Acaraú
Brazil	23	CE	2312106	Santana do Cariri
Brazil	23	CE	2312304	São Benedito
Brazil	23	CE	2312403	São Gonçalo do Amarante
Brazil	23	CE	2312502	São João do Jaguaribe
Brazil	23	CE	2312601	São Luís do Curu
Brazil	23	CE	2312700	Senador Pompeu
Brazil	23	CE	2312809	Senador Sá
Brazil	23	CE	2312908	Sobral
Brazil	23	CE	2313005	Solonópole
Brazil	23	CE	2313104	Tabuleiro do Norte
Brazil	23	CE	2313203	Tamboril
Brazil	23	CE	2313252	Tarrafas
Brazil	23	CE	2313302	Tauá
Brazil	23	CE	2313351	Tejuçuoca
Brazil	23	CE	2313401	Tianguá
Brazil	23	CE	2313500	Trairi
Brazil	23	CE	2313559	Tururu
Brazil	23	CE	2313609	Ubajara
Brazil	23	CE	2313708	Umari
Brazil	23	CE	2313757	Umirim
Brazil	23	CE	2313807	Uruburetama
Brazil	23	CE	2313906	Uruoca
Brazil	23	CE	2313955	Varjota
Brazil	23	CE	2314003	Várzea Alegre
Brazil	23	CE	2314102	Viçosa do Ceará
Brazil	26	PE	2600054	Abreu e Lima
Brazil	26	PE	2600104	Afogados da Ingazeira
Brazil	26	PE	2600203	Afrânio
Brazil	26	PE	2600302	Agrestina
Brazil	26	PE	2600401	Água Preta
Brazil	26	PE	2600500	Águas Belas
Brazil	26	PE	2600609	Alagoinha
Brazil	26	PE	2600708	Aliança
Brazil	26	PE	2600807	Altinho
Brazil	26	PE	2600906	Amaraji
Brazil	26	PE	2601003	Angelim
Brazil	26	PE	2601052	Araçoiaba
Brazil	26	PE	2601102	Araripina
Brazil	26	PE	2601201	Arcoverde
Brazil	26	PE	2601300	Barra de Guabiraba
Brazil	26	PE	2601409	Barreiros
Brazil	26	PE	2601508	Belém de Maria
Brazil	26	PE	2601607	Belém de São Francisco
Brazil	26	PE	2601706	Belo Jardim
Brazil	26	PE	2601805	Betânia
Brazil	26	PE	2601904	Bezerros
Brazil	26	PE	2602001	Bodocó
Brazil	26	PE	2602100	Bom Conselho
Brazil	26	PE	2602209	Bom Jardim
Brazil	26	PE	2602308	Bonito
Brazil	26	PE	2602407	Brejão
Brazil	26	PE	2602506	Brejinho
Brazil	26	PE	2602605	Brejo da Madre de Deus
Brazil	26	PE	2602704	Buenos Aires
Brazil	26	PE	2602803	Buíque
Brazil	26	PE	2602902	Cabo de Santo Agostinho
Brazil	26	PE	2603009	Cabrobó
Brazil	26	PE	2603108	Cachoeirinha
Brazil	26	PE	2603207	Caetés
Brazil	26	PE	2603306	Calçado
Brazil	26	PE	2603405	Calumbi
Brazil	26	PE	2603454	Camaragibe
Brazil	26	PE	2603504	Camocim de São Félix
Brazil	26	PE	2603603	Camutanga
Brazil	26	PE	2603702	Canhotinho
Brazil	26	PE	2603801	Capoeiras
Brazil	26	PE	2603900	Carnaíba
Brazil	26	PE	2603926	Carnaubeira da Penha
Brazil	26	PE	2604007	Carpina
Brazil	26	PE	2604106	Caruaru
Brazil	26	PE	2604155	Casinhas
Brazil	26	PE	2604205	Catende
Brazil	26	PE	2604304	Cedro
Brazil	26	PE	2604403	Chã de Alegria
Brazil	26	PE	2604502	Chã Grande
Brazil	26	PE	2604601	Condado
Brazil	26	PE	2604700	Correntes
Brazil	26	PE	2604809	Cortês
Brazil	26	PE	2604908	Cumaru
Brazil	26	PE	2605004	Cupira
Brazil	26	PE	2605103	Custódia
Brazil	26	PE	2605152	Dormentes
Brazil	26	PE	2605202	Escada
Brazil	26	PE	2605301	Exu
Brazil	26	PE	2605400	Feira Nova
Brazil	26	PE	2605459	Fernando de Noronha
Brazil	26	PE	2605509	Ferreiros
Brazil	26	PE	2605608	Flores
Brazil	26	PE	2605707	Floresta
Brazil	26	PE	2605806	Frei Miguelinho
Brazil	26	PE	2605905	Gameleira
Brazil	26	PE	2606002	Garanhuns
Brazil	26	PE	2606101	Glória do Goitá
Brazil	26	PE	2606200	Goiana
Brazil	26	PE	2606309	Granito
Brazil	26	PE	2606408	Gravatá
Brazil	26	PE	2606507	Iati
Brazil	26	PE	2606606	Ibimirim
Brazil	26	PE	2606705	Ibirajuba
Brazil	26	PE	2606804	Igarassu
Brazil	26	PE	2606903	Iguaraci
Brazil	26	PE	2607604	Ilha de Itamaracá
Brazil	26	PE	2607000	Inajá
Brazil	26	PE	2607109	Ingazeira
Brazil	26	PE	2607208	Ipojuca
Brazil	26	PE	2607307	Ipubi
Brazil	26	PE	2607406	Itacuruba
Brazil	26	PE	2607505	Itaíba
Brazil	26	PE	2607653	Itambé
Brazil	26	PE	2607703	Itapetim
Brazil	26	PE	2607752	Itapissuma
Brazil	26	PE	2607802	Itaquitinga
Brazil	26	PE	2607901	Jaboatão dos Guararapes
Brazil	26	PE	2607950	Jaqueira
Brazil	26	PE	2608008	Jataúba
Brazil	26	PE	2608057	Jatobá
Brazil	26	PE	2608107	João Alfredo
Brazil	26	PE	2608206	Joaquim Nabuco
Brazil	26	PE	2608255	Jucati
Brazil	26	PE	2608305	Jupi
Brazil	26	PE	2608404	Jurema
Brazil	26	PE	2608453	Lagoa do Carro
Brazil	26	PE	2608503	Lagoa do Itaenga
Brazil	26	PE	2608602	Lagoa do Ouro
Brazil	26	PE	2608701	Lagoa dos Gatos
Brazil	26	PE	2608750	Lagoa Grande
Brazil	26	PE	2608800	Lajedo
Brazil	26	PE	2608909	Limoeiro
Brazil	26	PE	2609006	Macaparana
Brazil	26	PE	2609105	Machados
Brazil	26	PE	2609154	Manari
Brazil	26	PE	2609204	Maraial
Brazil	26	PE	2609303	Mirandiba
Brazil	26	PE	2614303	Moreilândia
Brazil	26	PE	2609402	Moreno
Brazil	26	PE	2609501	Nazaré da Mata
Brazil	26	PE	2609600	Olinda
Brazil	26	PE	2609709	Orobó
Brazil	26	PE	2609808	Orocó
Brazil	26	PE	2609907	Ouricuri
Brazil	26	PE	2610004	Palmares
Brazil	26	PE	2610103	Palmeirina
Brazil	26	PE	2610202	Panelas
Brazil	26	PE	2610301	Paranatama
Brazil	26	PE	2610400	Parnamirim
Brazil	26	PE	2610509	Passira
Brazil	26	PE	2610608	Paudalho
Brazil	26	PE	2610707	Paulista
Brazil	26	PE	2610806	Pedra
Brazil	26	PE	2610905	Pesqueira
Brazil	26	PE	2611002	Petrolândia
Brazil	26	PE	2611101	Petrolina
Brazil	26	PE	2611200	Poção
Brazil	26	PE	2611309	Pombos
Brazil	26	PE	2611408	Primavera
Brazil	26	PE	2611507	Quipapá
Brazil	26	PE	2611533	Quixaba
Brazil	26	PE	2611606	Recife
Brazil	26	PE	2611705	Riacho das Almas
Brazil	26	PE	2611804	Ribeirão
Brazil	26	PE	2611903	Rio Formoso
Brazil	26	PE	2612000	Sairé
Brazil	26	PE	2612109	Salgadinho
Brazil	26	PE	2612208	Salgueiro
Brazil	26	PE	2612307	Saloá
Brazil	26	PE	2612406	Sanharó
Brazil	26	PE	2612455	Santa Cruz
Brazil	26	PE	2612471	Santa Cruz da Baixa Verde
Brazil	26	PE	2612505	Santa Cruz do Capibaribe
Brazil	26	PE	2612554	Santa Filomena
Brazil	26	PE	2612604	Santa Maria da Boa Vista
Brazil	26	PE	2612703	Santa Maria do Cambucá
Brazil	26	PE	2612802	Santa Terezinha
Brazil	26	PE	2612901	São Benedito do Sul
Brazil	26	PE	2613008	São Bento do Una
Brazil	26	PE	2613107	São Caitano
Brazil	26	PE	2613206	São João
Brazil	26	PE	2613305	São Joaquim do Monte
Brazil	26	PE	2613404	São José da Coroa Grande
Brazil	26	PE	2613503	São José do Belmonte
Brazil	26	PE	2613602	São José do Egito
Brazil	26	PE	2613701	São Lourenço da Mata
Brazil	26	PE	2613800	São Vicente Ferrer
Brazil	26	PE	2613909	Serra Talhada
Brazil	26	PE	2614006	Serrita
Brazil	26	PE	2614105	Sertânia
Brazil	26	PE	2614204	Sirinhaém
Brazil	26	PE	2614402	Solidão
Brazil	26	PE	2614501	Surubim
Brazil	26	PE	2614600	Tabira
Brazil	26	PE	2614709	Tacaimbó
Brazil	26	PE	2614808	Tacaratu
Brazil	26	PE	2614857	Tamandaré
Brazil	26	PE	2615003	Taquaritinga do Norte
Brazil	26	PE	2615102	Terezinha
Brazil	26	PE	2615201	Terra Nova
Brazil	26	PE	2615300	Timbaúba
Brazil	26	PE	2615409	Toritama
Brazil	26	PE	2615508	Tracunhaém
Brazil	26	PE	2615607	Trindade
Brazil	26	PE	2615706	Triunfo
Brazil	26	PE	2615805	Tupanatinga
Brazil	26	PE	2615904	Tuparetama
Brazil	26	PE	2616001	Venturosa
Brazil	26	PE	2616100	Verdejante
Brazil	26	PE	2616183	Vertente do Lério
Brazil	26	PE	2616209	Vertentes
Brazil	26	PE	2616308	Vicência
Brazil	26	PE	2616407	Vitória de Santo Antão
Brazil	26	PE	2616506	Xexéu
Brazil	21	MA	2100055	Açailândia
Brazil	21	MA	2100105	Afonso Cunha
Brazil	21	MA	2100154	Água Doce do Maranhão
Brazil	21	MA	2100204	Alcântara
Brazil	21	MA	2100303	Aldeias Altas
Brazil	21	MA	2100402	Altamira do Maranhão
Brazil	21	MA	2100436	Alto Alegre do Maranhão
Brazil	21	MA	2100477	Alto Alegre do Pindaré
Brazil	21	MA	2100501	Alto Parnaíba
Brazil	21	MA	2100550	Amapá do Maranhão
Brazil	21	MA	2100600	Amarante do Maranhão
Brazil	21	MA	2100709	Anajatuba
Brazil	21	MA	2100808	Anapurus
Brazil	21	MA	2100832	Apicum-Açu
Brazil	21	MA	2100873	Araguanã
Brazil	21	MA	2100907	Araioses
Brazil	21	MA	2100956	Arame
Brazil	21	MA	2101004	Arari
Brazil	21	MA	2101103	Axixá
Brazil	21	MA	2101202	Bacabal
Brazil	21	MA	2101251	Bacabeira
Brazil	21	MA	2101301	Bacuri
Brazil	21	MA	2101350	Bacurituba
Brazil	21	MA	2101400	Balsas
Brazil	21	MA	2101509	Barão de Grajaú
Brazil	21	MA	2101608	Barra do Corda
Brazil	21	MA	2101707	Barreirinhas
Brazil	21	MA	2101772	Bela Vista do Maranhão
Brazil	21	MA	2101731	Belágua
Brazil	21	MA	2101806	Benedito Leite
Brazil	21	MA	2101905	Bequimão
Brazil	21	MA	2101939	Bernardo do Mearim
Brazil	21	MA	2101970	Boa Vista do Gurupi
Brazil	21	MA	2102002	Bom Jardim
Brazil	21	MA	2102036	Bom Jesus das Selvas
Brazil	21	MA	2102077	Bom Lugar
Brazil	21	MA	2102101	Brejo
Brazil	21	MA	2102150	Brejo de Areia
Brazil	21	MA	2102200	Buriti
Brazil	21	MA	2102309	Buriti Bravo
Brazil	21	MA	2102325	Buriticupu
Brazil	21	MA	2102358	Buritirana
Brazil	21	MA	2102374	Cachoeira Grande
Brazil	21	MA	2102408	Cajapió
Brazil	21	MA	2102507	Cajari
Brazil	21	MA	2102556	Campestre do Maranhão
Brazil	21	MA	2102606	Cândido Mendes
Brazil	21	MA	2102705	Cantanhede
Brazil	21	MA	2102754	Capinzal do Norte
Brazil	21	MA	2102804	Carolina
Brazil	21	MA	2102903	Carutapera
Brazil	21	MA	2103000	Caxias
Brazil	21	MA	2103109	Cedral
Brazil	21	MA	2103125	Central do Maranhão
Brazil	21	MA	2103158	Centro do Guilherme
Brazil	21	MA	2103174	Centro Novo do Maranhão
Brazil	21	MA	2103208	Chapadinha
Brazil	21	MA	2103257	Cidelândia
Brazil	21	MA	2103307	Codó
Brazil	21	MA	2103406	Coelho Neto
Brazil	21	MA	2103505	Colinas
Brazil	21	MA	2103554	Conceição do Lago-Açu
Brazil	21	MA	2103604	Coroatá
Brazil	21	MA	2103703	Cururupu
Brazil	21	MA	2103752	Davinópolis
Brazil	21	MA	2103802	Dom Pedro
Brazil	21	MA	2103901	Duque Bacelar
Brazil	21	MA	2104008	Esperantinópolis
Brazil	21	MA	2104057	Estreito
Brazil	21	MA	2104073	Feira Nova do Maranhão
Brazil	21	MA	2104081	Fernando Falcão
Brazil	21	MA	2104099	Formosa da Serra Negra
Brazil	21	MA	2104107	Fortaleza dos Nogueiras
Brazil	21	MA	2104206	Fortuna
Brazil	21	MA	2104305	Godofredo Viana
Brazil	21	MA	2104404	Gonçalves Dias
Brazil	21	MA	2104503	Governador Archer
Brazil	21	MA	2104552	Governador Edison Lobão
Brazil	21	MA	2104602	Governador Eugênio Barros
Brazil	21	MA	2104628	Governador Luiz Rocha
Brazil	21	MA	2104651	Governador Newton Bello
Brazil	21	MA	2104677	Governador Nunes Freire
Brazil	21	MA	2104701	Graça Aranha
Brazil	21	MA	2104800	Grajaú
Brazil	21	MA	2104909	Guimarães
Brazil	21	MA	2105005	Humberto de Campos
Brazil	21	MA	2105104	Icatu
Brazil	21	MA	2105153	Igarapé do Meio
Brazil	21	MA	2105203	Igarapé Grande
Brazil	21	MA	2105302	Imperatriz
Brazil	21	MA	2105351	Itaipava do Grajaú
Brazil	21	MA	2105401	Itapecuru Mirim
Brazil	21	MA	2105427	Itinga do Maranhão
Brazil	21	MA	2105450	Jatobá
Brazil	21	MA	2105476	Jenipapo dos Vieiras
Brazil	21	MA	2105500	João Lisboa
Brazil	21	MA	2105609	Joselândia
Brazil	21	MA	2105658	Junco do Maranhão
Brazil	21	MA	2105708	Lago da Pedra
Brazil	21	MA	2105807	Lago do Junco
Brazil	21	MA	2105948	Lago dos Rodrigues
Brazil	21	MA	2105906	Lago Verde
Brazil	21	MA	2105922	Lagoa do Mato
Brazil	21	MA	2105963	Lagoa Grande do Maranhão
Brazil	21	MA	2105989	Lajeado Novo
Brazil	21	MA	2106003	Lima Campos
Brazil	21	MA	2106102	Loreto
Brazil	21	MA	2106201	Luís Domingues
Brazil	21	MA	2106300	Magalhães de Almeida
Brazil	21	MA	2106326	Maracaçumé
Brazil	21	MA	2106359	Marajá do Sena
Brazil	21	MA	2106375	Maranhãozinho
Brazil	21	MA	2106409	Mata Roma
Brazil	21	MA	2106508	Matinha
Brazil	21	MA	2106607	Matões
Brazil	21	MA	2106631	Matões do Norte
Brazil	21	MA	2106672	Milagres do Maranhão
Brazil	21	MA	2106706	Mirador
Brazil	21	MA	2106755	Miranda do Norte
Brazil	21	MA	2106805	Mirinzal
Brazil	21	MA	2106904	Monção
Brazil	21	MA	2107001	Montes Altos
Brazil	21	MA	2107100	Morros
Brazil	21	MA	2107209	Nina Rodrigues
Brazil	21	MA	2107258	Nova Colinas
Brazil	21	MA	2107308	Nova Iorque
Brazil	21	MA	2107357	Nova Olinda do Maranhão
Brazil	21	MA	2107407	Olho d'Água das Cunhãs
Brazil	21	MA	2107456	Olinda Nova do Maranhão
Brazil	21	MA	2107506	Paço do Lumiar
Brazil	21	MA	2107605	Palmeirândia
Brazil	21	MA	2107704	Paraibano
Brazil	21	MA	2107803	Parnarama
Brazil	21	MA	2107902	Passagem Franca
Brazil	21	MA	2108009	Pastos Bons
Brazil	21	MA	2108058	Paulino Neves
Brazil	21	MA	2108108	Paulo Ramos
Brazil	21	MA	2108207	Pedreiras
Brazil	21	MA	2108256	Pedro do Rosário
Brazil	21	MA	2108306	Penalva
Brazil	21	MA	2108405	Peri Mirim
Brazil	21	MA	2108454	Peritoró
Brazil	21	MA	2108504	Pindaré-Mirim
Brazil	21	MA	2108603	Pinheiro
Brazil	21	MA	2108702	Pio XII
Brazil	21	MA	2108801	Pirapemas
Brazil	21	MA	2108900	Poção de Pedras
Brazil	21	MA	2109007	Porto Franco
Brazil	21	MA	2109056	Porto Rico do Maranhão
Brazil	21	MA	2109106	Presidente Dutra
Brazil	21	MA	2109205	Presidente Juscelino
Brazil	21	MA	2109239	Presidente Médici
Brazil	21	MA	2109270	Presidente Sarney
Brazil	21	MA	2109304	Presidente Vargas
Brazil	21	MA	2109403	Primeira Cruz
Brazil	21	MA	2109452	Raposa
Brazil	21	MA	2109502	Riachão
Brazil	21	MA	2109551	Ribamar Fiquene
Brazil	21	MA	2109601	Rosário
Brazil	21	MA	2109700	Sambaíba
Brazil	21	MA	2109759	Santa Filomena do Maranhão
Brazil	21	MA	2109809	Santa Helena
Brazil	21	MA	2109908	Santa Inês
Brazil	21	MA	2110005	Santa Luzia
Brazil	21	MA	2110039	Santa Luzia do Paruá
Brazil	21	MA	2110104	Santa Quitéria do Maranhão
Brazil	21	MA	2110203	Santa Rita
Brazil	21	MA	2110237	Santana do Maranhão
Brazil	21	MA	2110278	Santo Amaro do Maranhão
Brazil	21	MA	2110302	Santo Antônio dos Lopes
Brazil	21	MA	2110401	São Benedito do Rio Preto
Brazil	21	MA	2110500	São Bento
Brazil	21	MA	2110609	São Bernardo
Brazil	21	MA	2110658	São Domingos do Azeitão
Brazil	21	MA	2110708	São Domingos do Maranhão
Brazil	21	MA	2110807	São Félix de Balsas
Brazil	21	MA	2110856	São Francisco do Brejão
Brazil	21	MA	2110906	São Francisco do Maranhão
Brazil	21	MA	2111003	São João Batista
Brazil	21	MA	2111029	São João do Carú
Brazil	21	MA	2111052	São João do Paraíso
Brazil	21	MA	2111078	São João do Soter
Brazil	21	MA	2111102	São João dos Patos
Brazil	21	MA	2111201	São José de Ribamar
Brazil	21	MA	2111250	São José dos Basílios
Brazil	21	MA	2111300	São Luís
Brazil	21	MA	2111409	São Luís Gonzaga do Maranhão
Brazil	21	MA	2111508	São Mateus do Maranhão
Brazil	21	MA	2111532	São Pedro da Água Branca
Brazil	21	MA	2111573	São Pedro dos Crentes
Brazil	21	MA	2111607	São Raimundo das Mangabeiras
Brazil	21	MA	2111631	São Raimundo do Doca Bezerra
Brazil	21	MA	2111672	São Roberto
Brazil	21	MA	2111706	São Vicente Ferrer
Brazil	21	MA	2111722	Satubinha
Brazil	21	MA	2111748	Senador Alexandre Costa
Brazil	21	MA	2111763	Senador La Rocque
Brazil	21	MA	2111789	Serrano do Maranhão
Brazil	21	MA	2111805	Sítio Novo
Brazil	21	MA	2111904	Sucupira do Norte
Brazil	21	MA	2111953	Sucupira do Riachão
Brazil	21	MA	2112001	Tasso Fragoso
Brazil	21	MA	2112100	Timbiras
Brazil	21	MA	2112209	Timon
Brazil	21	MA	2112233	Trizidela do Vale
Brazil	21	MA	2112274	Tufilândia
Brazil	21	MA	2112308	Tuntum
Brazil	21	MA	2112407	Turiaçu
Brazil	21	MA	2112456	Turilândia
Brazil	21	MA	2112506	Tutóia
Brazil	21	MA	2112605	Urbano Santos
Brazil	21	MA	2112704	Vargem Grande
Brazil	21	MA	2112803	Viana
Brazil	21	MA	2112852	Vila Nova dos Martírios
Brazil	21	MA	2112902	Vitória do Mearim
Brazil	21	MA	2113009	Vitorino Freire
Brazil	21	MA	2114007	Zé Doca
Brazil	22	PI	2200053	Acauã
Brazil	22	PI	2200103	Agricolândia
Brazil	22	PI	2200202	Água Branca
Brazil	22	PI	2200251	Alagoinha do Piauí
Brazil	22	PI	2200277	Alegrete do Piauí
Brazil	22	PI	2200301	Alto Longá
Brazil	22	PI	2200400	Altos
Brazil	22	PI	2200459	Alvorada do Gurguéia
Brazil	22	PI	2200509	Amarante
Brazil	22	PI	2200608	Angical do Piauí
Brazil	22	PI	2200707	Anísio de Abreu
Brazil	22	PI	2200806	Antônio Almeida
Brazil	22	PI	2200905	Aroazes
Brazil	22	PI	2200954	Aroeiras do Itaim
Brazil	22	PI	2201002	Arraial
Brazil	22	PI	2201051	Assunção do Piauí
Brazil	22	PI	2201101	Avelino Lopes
Brazil	22	PI	2201150	Baixa Grande do Ribeiro
Brazil	22	PI	2201176	Barra D'Alcântara
Brazil	22	PI	2201200	Barras
Brazil	22	PI	2201309	Barreiras do Piauí
Brazil	22	PI	2201408	Barro Duro
Brazil	22	PI	2201507	Batalha
Brazil	22	PI	2201556	Bela Vista do Piauí
Brazil	22	PI	2201572	Belém do Piauí
Brazil	22	PI	2201606	Beneditinos
Brazil	22	PI	2201705	Bertolínia
Brazil	22	PI	2201739	Betânia do Piauí
Brazil	22	PI	2201770	Boa Hora
Brazil	22	PI	2201804	Bocaina
Brazil	22	PI	2201903	Bom Jesus
Brazil	22	PI	2201919	Bom Princípio do Piauí
Brazil	22	PI	2201929	Bonfim do Piauí
Brazil	22	PI	2201945	Boqueirão do Piauí
Brazil	22	PI	2201960	Brasileira
Brazil	22	PI	2201988	Brejo do Piauí
Brazil	22	PI	2202000	Buriti dos Lopes
Brazil	22	PI	2202026	Buriti dos Montes
Brazil	22	PI	2202059	Cabeceiras do Piauí
Brazil	22	PI	2202075	Cajazeiras do Piauí
Brazil	22	PI	2202083	Cajueiro da Praia
Brazil	22	PI	2202091	Caldeirão Grande do Piauí
Brazil	22	PI	2202109	Campinas do Piauí
Brazil	22	PI	2202117	Campo Alegre do Fidalgo
Brazil	22	PI	2202133	Campo Grande do Piauí
Brazil	22	PI	2202174	Campo Largo do Piauí
Brazil	22	PI	2202208	Campo Maior
Brazil	22	PI	2202251	Canavieira
Brazil	22	PI	2202307	Canto do Buriti
Brazil	22	PI	2202406	Capitão de Campos
Brazil	22	PI	2202455	Capitão Gervásio Oliveira
Brazil	22	PI	2202505	Caracol
Brazil	22	PI	2202539	Caraúbas do Piauí
Brazil	22	PI	2202554	Caridade do Piauí
Brazil	22	PI	2202604	Castelo do Piauí
Brazil	22	PI	2202653	Caxingó
Brazil	22	PI	2202703	Cocal
Brazil	22	PI	2202711	Cocal de Telha
Brazil	22	PI	2202729	Cocal dos Alves
Brazil	22	PI	2202737	Coivaras
Brazil	22	PI	2202752	Colônia do Gurguéia
Brazil	22	PI	2202778	Colônia do Piauí
Brazil	22	PI	2202802	Conceição do Canindé
Brazil	22	PI	2202851	Coronel José Dias
Brazil	22	PI	2202901	Corrente
Brazil	22	PI	2203008	Cristalândia do Piauí
Brazil	22	PI	2203107	Cristino Castro
Brazil	22	PI	2203206	Curimatá
Brazil	22	PI	2203230	Currais
Brazil	22	PI	2203271	Curral Novo do Piauí
Brazil	22	PI	2203255	Curralinhos
Brazil	22	PI	2203305	Demerval Lobão
Brazil	22	PI	2203354	Dirceu Arcoverde
Brazil	22	PI	2203404	Dom Expedito Lopes
Brazil	22	PI	2203453	Dom Inocêncio
Brazil	22	PI	2203420	Domingos Mourão
Brazil	22	PI	2203503	Elesbão Veloso
Brazil	22	PI	2203602	Eliseu Martins
Brazil	22	PI	2203701	Esperantina
Brazil	22	PI	2203750	Fartura do Piauí
Brazil	22	PI	2203800	Flores do Piauí
Brazil	22	PI	2203859	Floresta do Piauí
Brazil	22	PI	2203909	Floriano
Brazil	22	PI	2204006	Francinópolis
Brazil	22	PI	2204105	Francisco Ayres
Brazil	22	PI	2204154	Francisco Macedo
Brazil	22	PI	2204204	Francisco Santos
Brazil	22	PI	2204303	Fronteiras
Brazil	22	PI	2204352	Geminiano
Brazil	22	PI	2204402	Gilbués
Brazil	22	PI	2204501	Guadalupe
Brazil	22	PI	2204550	Guaribas
Brazil	22	PI	2204600	Hugo Napoleão
Brazil	22	PI	2204659	Ilha Grande
Brazil	22	PI	2204709	Inhuma
Brazil	22	PI	2204808	Ipiranga do Piauí
Brazil	22	PI	2204907	Isaías Coelho
Brazil	22	PI	2205003	Itainópolis
Brazil	22	PI	2205102	Itaueira
Brazil	22	PI	2205151	Jacobina do Piauí
Brazil	22	PI	2205201	Jaicós
Brazil	22	PI	2205250	Jardim do Mulato
Brazil	22	PI	2205276	Jatobá do Piauí
Brazil	22	PI	2205300	Jerumenha
Brazil	22	PI	2205359	João Costa
Brazil	22	PI	2205409	Joaquim Pires
Brazil	22	PI	2205458	Joca Marques
Brazil	22	PI	2205508	José de Freitas
Brazil	22	PI	2205516	Juazeiro do Piauí
Brazil	22	PI	2205524	Júlio Borges
Brazil	22	PI	2205532	Jurema
Brazil	22	PI	2205557	Lagoa Alegre
Brazil	22	PI	2205573	Lagoa de São Francisco
Brazil	22	PI	2205565	Lagoa do Barro do Piauí
Brazil	22	PI	2205581	Lagoa do Piauí
Brazil	22	PI	2205599	Lagoa do Sítio
Brazil	22	PI	2205540	Lagoinha do Piauí
Brazil	22	PI	2205607	Landri Sales
Brazil	22	PI	2205706	Luís Correia
Brazil	22	PI	2205805	Luzilândia
Brazil	22	PI	2205854	Madeiro
Brazil	22	PI	2205904	Manoel Emídio
Brazil	22	PI	2205953	Marcolândia
Brazil	22	PI	2206001	Marcos Parente
Brazil	22	PI	2206050	Massapê do Piauí
Brazil	22	PI	2206100	Matias Olímpio
Brazil	22	PI	2206209	Miguel Alves
Brazil	22	PI	2206308	Miguel Leão
Brazil	22	PI	2206357	Milton Brandão
Brazil	22	PI	2206407	Monsenhor Gil
Brazil	22	PI	2206506	Monsenhor Hipólito
Brazil	22	PI	2206605	Monte Alegre do Piauí
Brazil	22	PI	2206654	Morro Cabeça no Tempo
Brazil	22	PI	2206670	Morro do Chapéu do Piauí
Brazil	22	PI	2206696	Murici dos Portelas
Brazil	22	PI	2206704	Nazaré do Piauí
Brazil	22	PI	2206720	Nazária
Brazil	22	PI	2206753	Nossa Senhora de Nazaré
Brazil	22	PI	2206803	Nossa Senhora dos Remédios
Brazil	22	PI	2207959	Nova Santa Rita
Brazil	22	PI	2206902	Novo Oriente do Piauí
Brazil	22	PI	2206951	Novo Santo Antônio
Brazil	22	PI	2207009	Oeiras
Brazil	22	PI	2207108	Olho D'Água do Piauí
Brazil	22	PI	2207207	Padre Marcos
Brazil	22	PI	2207306	Paes Landim
Brazil	22	PI	2207355	Pajeú do Piauí
Brazil	22	PI	2207405	Palmeira do Piauí
Brazil	22	PI	2207504	Palmeirais
Brazil	22	PI	2207553	Paquetá
Brazil	22	PI	2207603	Parnaguá
Brazil	22	PI	2207702	Parnaíba
Brazil	22	PI	2207751	Passagem Franca do Piauí
Brazil	22	PI	2207777	Patos do Piauí
Brazil	22	PI	2207793	Pau D'Arco do Piauí
Brazil	22	PI	2207801	Paulistana
Brazil	22	PI	2207850	Pavussu
Brazil	22	PI	2207900	Pedro II
Brazil	22	PI	2207934	Pedro Laurentino
Brazil	22	PI	2208007	Picos
Brazil	22	PI	2208106	Pimenteiras
Brazil	22	PI	2208205	Pio IX
Brazil	22	PI	2208304	Piracuruca
Brazil	22	PI	2208403	Piripiri
Brazil	22	PI	2208502	Porto
Brazil	22	PI	2208551	Porto Alegre do Piauí
Brazil	22	PI	2208601	Prata do Piauí
Brazil	22	PI	2208650	Queimada Nova
Brazil	22	PI	2208700	Redenção do Gurguéia
Brazil	22	PI	2208809	Regeneração
Brazil	22	PI	2208858	Riacho Frio
Brazil	22	PI	2208874	Ribeira do Piauí
Brazil	22	PI	2208908	Ribeiro Gonçalves
Brazil	22	PI	2209005	Rio Grande do Piauí
Brazil	22	PI	2209104	Santa Cruz do Piauí
Brazil	22	PI	2209153	Santa Cruz dos Milagres
Brazil	22	PI	2209203	Santa Filomena
Brazil	22	PI	2209302	Santa Luz
Brazil	22	PI	2209377	Santa Rosa do Piauí
Brazil	22	PI	2209351	Santana do Piauí
Brazil	22	PI	2209401	Santo Antônio de Lisboa
Brazil	22	PI	2209450	Santo Antônio dos Milagres
Brazil	22	PI	2209500	Santo Inácio do Piauí
Brazil	22	PI	2209559	São Braz do Piauí
Brazil	22	PI	2209609	São Félix do Piauí
Brazil	22	PI	2209658	São Francisco de Assis do Piauí
Brazil	22	PI	2209708	São Francisco do Piauí
Brazil	22	PI	2209757	São Gonçalo do Gurguéia
Brazil	22	PI	2209807	São Gonçalo do Piauí
Brazil	22	PI	2209856	São João da Canabrava
Brazil	22	PI	2209872	São João da Fronteira
Brazil	22	PI	2209906	São João da Serra
Brazil	22	PI	2209955	São João da Varjota
Brazil	22	PI	2209971	São João do Arraial
Brazil	22	PI	2210003	São João do Piauí
Brazil	22	PI	2210052	São José do Divino
Brazil	22	PI	2210102	São José do Peixe
Brazil	22	PI	2210201	São José do Piauí
Brazil	22	PI	2210300	São Julião
Brazil	22	PI	2210359	São Lourenço do Piauí
Brazil	22	PI	2210375	São Luis do Piauí
Brazil	22	PI	2210383	São Miguel da Baixa Grande
Brazil	22	PI	2210391	São Miguel do Fidalgo
Brazil	22	PI	2210409	São Miguel do Tapuio
Brazil	22	PI	2210508	São Pedro do Piauí
Brazil	22	PI	2210607	São Raimundo Nonato
Brazil	22	PI	2210623	Sebastião Barros
Brazil	22	PI	2210631	Sebastião Leal
Brazil	22	PI	2210656	Sigefredo Pacheco
Brazil	22	PI	2210706	Simões
Brazil	22	PI	2210805	Simplício Mendes
Brazil	22	PI	2210904	Socorro do Piauí
Brazil	22	PI	2210938	Sussuapara
Brazil	22	PI	2210953	Tamboril do Piauí
Brazil	22	PI	2210979	Tanque do Piauí
Brazil	22	PI	2211001	Teresina
Brazil	22	PI	2211100	União
Brazil	22	PI	2211209	Uruçuí
Brazil	22	PI	2211308	Valença do Piauí
Brazil	22	PI	2211357	Várzea Branca
Brazil	22	PI	2211407	Várzea Grande
Brazil	22	PI	2211506	Vera Mendes
Brazil	22	PI	2211605	Vila Nova do Piauí
Brazil	22	PI	2211704	Wall Ferraz
Brazil	25	PB	2500106	Água Branca
Brazil	25	PB	2500205	Aguiar
Brazil	25	PB	2500304	Alagoa Grande
Brazil	25	PB	2500403	Alagoa Nova
Brazil	25	PB	2500502	Alagoinha
Brazil	25	PB	2500536	Alcantil
Brazil	25	PB	2500577	Algodão de Jandaíra
Brazil	25	PB	2500601	Alhandra
Brazil	25	PB	2500734	Amparo
Brazil	25	PB	2500775	Aparecida
Brazil	25	PB	2500809	Araçagi
Brazil	25	PB	2500908	Arara
Brazil	25	PB	2501005	Araruna
Brazil	25	PB	2501104	Areia
Brazil	25	PB	2501153	Areia de Baraúnas
Brazil	25	PB	2501203	Areial
Brazil	25	PB	2501302	Aroeiras
Brazil	25	PB	2501351	Assunção
Brazil	25	PB	2501401	Baía da Traição
Brazil	25	PB	2501500	Bananeiras
Brazil	25	PB	2501534	Baraúna
Brazil	25	PB	2501609	Barra de Santa Rosa
Brazil	25	PB	2501575	Barra de Santana
Brazil	25	PB	2501708	Barra de São Miguel
Brazil	25	PB	2501807	Bayeux
Brazil	25	PB	2501906	Belém
Brazil	25	PB	2502003	Belém do Brejo do Cruz
Brazil	25	PB	2502052	Bernardino Batista
Brazil	25	PB	2502102	Boa Ventura
Brazil	25	PB	2502151	Boa Vista
Brazil	25	PB	2502201	Bom Jesus
Brazil	25	PB	2502300	Bom Sucesso
Brazil	25	PB	2502409	Bonito de Santa Fé
Brazil	25	PB	2502508	Boqueirão
Brazil	25	PB	2502706	Borborema
Brazil	25	PB	2502805	Brejo do Cruz
Brazil	25	PB	2502904	Brejo dos Santos
Brazil	25	PB	2503001	Caaporã
Brazil	25	PB	2503100	Cabaceiras
Brazil	25	PB	2503209	Cabedelo
Brazil	25	PB	2503308	Cachoeira dos Índios
Brazil	25	PB	2503407	Cacimba de Areia
Brazil	25	PB	2503506	Cacimba de Dentro
Brazil	25	PB	2503555	Cacimbas
Brazil	25	PB	2503605	Caiçara
Brazil	25	PB	2503704	Cajazeiras
Brazil	25	PB	2503753	Cajazeirinhas
Brazil	25	PB	2503803	Caldas Brandão
Brazil	25	PB	2503902	Camalaú
Brazil	25	PB	2504009	Campina Grande
Brazil	25	PB	2516409	Campo de Santana
Brazil	25	PB	2504033	Capim
Brazil	25	PB	2504074	Caraúbas
Brazil	25	PB	2504108	Carrapateira
Brazil	25	PB	2504157	Casserengue
Brazil	25	PB	2504207	Catingueira
Brazil	25	PB	2504306	Catolé do Rocha
Brazil	25	PB	2504355	Caturité
Brazil	25	PB	2504405	Conceição
Brazil	25	PB	2504504	Condado
Brazil	25	PB	2504603	Conde
Brazil	25	PB	2504702	Congo
Brazil	25	PB	2504801	Coremas
Brazil	25	PB	2504850	Coxixola
Brazil	25	PB	2504900	Cruz do Espírito Santo
Brazil	25	PB	2505006	Cubati
Brazil	25	PB	2505105	Cuité
Brazil	25	PB	2505238	Cuité de Mamanguape
Brazil	25	PB	2505204	Cuitegi
Brazil	25	PB	2505279	Curral de Cima
Brazil	25	PB	2505303	Curral Velho
Brazil	25	PB	2505352	Damião
Brazil	25	PB	2505402	Desterro
Brazil	25	PB	2505600	Diamante
Brazil	25	PB	2505709	Dona Inês
Brazil	25	PB	2505808	Duas Estradas
Brazil	25	PB	2505907	Emas
Brazil	25	PB	2506004	Esperança
Brazil	25	PB	2506103	Fagundes
Brazil	25	PB	2506202	Frei Martinho
Brazil	25	PB	2506251	Gado Bravo
Brazil	25	PB	2506301	Guarabira
Brazil	25	PB	2506400	Gurinhém
Brazil	25	PB	2506509	Gurjão
Brazil	25	PB	2506608	Ibiara
Brazil	25	PB	2502607	Igaracy
Brazil	25	PB	2506707	Imaculada
Brazil	25	PB	2506806	Ingá
Brazil	25	PB	2506905	Itabaiana
Brazil	25	PB	2507002	Itaporanga
Brazil	25	PB	2507101	Itapororoca
Brazil	25	PB	2507200	Itatuba
Brazil	25	PB	2507309	Jacaraú
Brazil	25	PB	2507408	Jericó
Brazil	25	PB	2507507	João Pessoa
Brazil	25	PB	2507606	Juarez Távora
Brazil	25	PB	2507705	Juazeirinho
Brazil	25	PB	2507804	Junco do Seridó
Brazil	25	PB	2507903	Juripiranga
Brazil	25	PB	2508000	Juru
Brazil	25	PB	2508109	Lagoa
Brazil	25	PB	2508208	Lagoa de Dentro
Brazil	25	PB	2508307	Lagoa Seca
Brazil	25	PB	2508406	Lastro
Brazil	25	PB	2508505	Livramento
Brazil	25	PB	2508554	Logradouro
Brazil	25	PB	2508604	Lucena
Brazil	25	PB	2508703	Mãe d'Água
Brazil	25	PB	2508802	Malta
Brazil	25	PB	2508901	Mamanguape
Brazil	25	PB	2509008	Manaíra
Brazil	25	PB	2509057	Marcação
Brazil	25	PB	2509107	Mari
Brazil	25	PB	2509156	Marizópolis
Brazil	25	PB	2509206	Massaranduba
Brazil	25	PB	2509305	Mataraca
Brazil	25	PB	2509339	Matinhas
Brazil	25	PB	2509370	Mato Grosso
Brazil	25	PB	2509396	Maturéia
Brazil	25	PB	2509404	Mogeiro
Brazil	25	PB	2509503	Montadas
Brazil	25	PB	2509602	Monte Horebe
Brazil	25	PB	2509701	Monteiro
Brazil	25	PB	2509800	Mulungu
Brazil	25	PB	2509909	Natuba
Brazil	25	PB	2510006	Nazarezinho
Brazil	25	PB	2510105	Nova Floresta
Brazil	25	PB	2510204	Nova Olinda
Brazil	25	PB	2510303	Nova Palmeira
Brazil	25	PB	2510402	Olho d'Água
Brazil	25	PB	2510501	Olivedos
Brazil	25	PB	2510600	Ouro Velho
Brazil	25	PB	2510659	Parari
Brazil	25	PB	2510709	Passagem
Brazil	25	PB	2510808	Patos
Brazil	25	PB	2510907	Paulista
Brazil	25	PB	2511004	Pedra Branca
Brazil	25	PB	2511103	Pedra Lavrada
Brazil	25	PB	2511202	Pedras de Fogo
Brazil	25	PB	2512721	Pedro Régis
Brazil	25	PB	2511301	Piancó
Brazil	25	PB	2511400	Picuí
Brazil	25	PB	2511509	Pilar
Brazil	25	PB	2511608	Pilões
Brazil	25	PB	2511707	Pilõezinhos
Brazil	25	PB	2511806	Pirpirituba
Brazil	25	PB	2511905	Pitimbu
Brazil	25	PB	2512002	Pocinhos
Brazil	25	PB	2512036	Poço Dantas
Brazil	25	PB	2512077	Poço de José de Moura
Brazil	25	PB	2512101	Pombal
Brazil	25	PB	2512200	Prata
Brazil	25	PB	2512309	Princesa Isabel
Brazil	25	PB	2512408	Puxinanã
Brazil	25	PB	2512507	Queimadas
Brazil	25	PB	2512606	Quixabá
Brazil	25	PB	2512705	Remígio
Brazil	25	PB	2512747	Riachão
Brazil	25	PB	2512754	Riachão do Bacamarte
Brazil	25	PB	2512762	Riachão do Poço
Brazil	25	PB	2512788	Riacho de Santo Antônio
Brazil	25	PB	2512804	Riacho dos Cavalos
Brazil	25	PB	2512903	Rio Tinto
Brazil	25	PB	2513000	Salgadinho
Brazil	25	PB	2513109	Salgado de São Félix
Brazil	25	PB	2513158	Santa Cecília
Brazil	25	PB	2513208	Santa Cruz
Brazil	25	PB	2513307	Santa Helena
Brazil	25	PB	2513356	Santa Inês
Brazil	25	PB	2513406	Santa Luzia
Brazil	25	PB	2513703	Santa Rita
Brazil	25	PB	2513802	Santa Teresinha
Brazil	25	PB	2513505	Santana de Mangueira
Brazil	25	PB	2513604	Santana dos Garrotes
Brazil	25	PB	2513653	Santarém
Brazil	25	PB	2513851	Santo André
Brazil	25	PB	2513927	São Bentinho
Brazil	25	PB	2513901	São Bento
Brazil	25	PB	2513968	São Domingos de Pombal
Brazil	25	PB	2513943	São Domingos do Cariri
Brazil	25	PB	2513984	São Francisco
Brazil	25	PB	2514008	São João do Cariri
Brazil	25	PB	2500700	São João do Rio do Peixe
Brazil	25	PB	2514107	São João do Tigre
Brazil	25	PB	2514206	São José da Lagoa Tapada
Brazil	25	PB	2514305	São José de Caiana
Brazil	25	PB	2514404	São José de Espinharas
Brazil	25	PB	2514503	São José de Piranhas
Brazil	25	PB	2514552	São José de Princesa
Brazil	25	PB	2514602	São José do Bonfim
Brazil	25	PB	2514651	São José do Brejo do Cruz
Brazil	25	PB	2514701	São José do Sabugi
Brazil	25	PB	2514800	São José dos Cordeiros
Brazil	25	PB	2514453	São José dos Ramos
Brazil	25	PB	2514909	São Mamede
Brazil	25	PB	2515005	São Miguel de Taipu
Brazil	25	PB	2515104	São Sebastião de Lagoa de Roça
Brazil	25	PB	2515203	São Sebastião do Umbuzeiro
Brazil	25	PB	2515302	Sapé
Brazil	25	PB	2515401	Seridó
Brazil	25	PB	2515500	Serra Branca
Brazil	25	PB	2515609	Serra da Raiz
Brazil	25	PB	2515708	Serra Grande
Brazil	25	PB	2515807	Serra Redonda
Brazil	25	PB	2515906	Serraria
Brazil	25	PB	2515930	Sertãozinho
Brazil	25	PB	2515971	Sobrado
Brazil	25	PB	2516003	Solânea
Brazil	25	PB	2516102	Soledade
Brazil	25	PB	2516151	Sossêgo
Brazil	25	PB	2516201	Sousa
Brazil	25	PB	2516300	Sumé
Brazil	25	PB	2516508	Taperoá
Brazil	25	PB	2516607	Tavares
Brazil	25	PB	2516706	Teixeira
Brazil	25	PB	2516755	Tenório
Brazil	25	PB	2516805	Triunfo
Brazil	25	PB	2516904	Uiraúna
Brazil	25	PB	2517001	Umbuzeiro
Brazil	25	PB	2517100	Várzea
Brazil	25	PB	2517209	Vieirópolis
Brazil	25	PB	2505501	Vista Serrana
Brazil	25	PB	2517407	Zabelê
Brazil	52	GO	5200050	Abadia de Goiás
Brazil	52	GO	5200100	Abadiânia
Brazil	52	GO	5200134	Acreúna
Brazil	52	GO	5200159	Adelândia
Brazil	52	GO	5200175	Água Fria de Goiás
Brazil	52	GO	5200209	Água Limpa
Brazil	52	GO	5200258	Águas Lindas de Goiás
Brazil	52	GO	5200308	Alexânia
Brazil	52	GO	5200506	Aloândia
Brazil	52	GO	5200555	Alto Horizonte
Brazil	52	GO	5200605	Alto Paraíso de Goiás
Brazil	52	GO	5200803	Alvorada do Norte
Brazil	52	GO	5200829	Amaralina
Brazil	52	GO	5200852	Americano do Brasil
Brazil	52	GO	5200902	Amorinópolis
Brazil	52	GO	5201108	Anápolis
Brazil	52	GO	5201207	Anhanguera
Brazil	52	GO	5201306	Anicuns
Brazil	52	GO	5201405	Aparecida de Goiânia
Brazil	52	GO	5201454	Aparecida do Rio Doce
Brazil	52	GO	5201504	Aporé
Brazil	52	GO	5201603	Araçu
Brazil	52	GO	5201702	Aragarças
Brazil	52	GO	5201801	Aragoiânia
Brazil	52	GO	5202155	Araguapaz
Brazil	52	GO	5202353	Arenópolis
Brazil	52	GO	5202502	Aruanã
Brazil	52	GO	5202601	Aurilândia
Brazil	52	GO	5202809	Avelinópolis
Brazil	52	GO	5203104	Baliza
Brazil	52	GO	5203203	Barro Alto
Brazil	52	GO	5203302	Bela Vista de Goiás
Brazil	52	GO	5203401	Bom Jardim de Goiás
Brazil	52	GO	5203500	Bom Jesus de Goiás
Brazil	52	GO	5203559	Bonfinópolis
Brazil	52	GO	5203575	Bonópolis
Brazil	52	GO	5203609	Brazabrantes
Brazil	52	GO	5203807	Britânia
Brazil	52	GO	5203906	Buriti Alegre
Brazil	52	GO	5203939	Buriti de Goiás
Brazil	52	GO	5203962	Buritinópolis
Brazil	52	GO	5204003	Cabeceiras
Brazil	52	GO	5204102	Cachoeira Alta
Brazil	52	GO	5204201	Cachoeira de Goiás
Brazil	52	GO	5204250	Cachoeira Dourada
Brazil	52	GO	5204300	Caçu
Brazil	52	GO	5204409	Caiapônia
Brazil	52	GO	5204508	Caldas Novas
Brazil	52	GO	5204557	Caldazinha
Brazil	52	GO	5204607	Campestre de Goiás
Brazil	52	GO	5204656	Campinaçu
Brazil	52	GO	5204706	Campinorte
Brazil	52	GO	5204805	Campo Alegre de Goiás
Brazil	52	GO	5204854	Campo Limpo de Goiás
Brazil	52	GO	5204904	Campos Belos
Brazil	52	GO	5204953	Campos Verdes
Brazil	52	GO	5205000	Carmo do Rio Verde
Brazil	52	GO	5205059	Castelândia
Brazil	52	GO	5205109	Catalão
Brazil	52	GO	5205208	Caturaí
Brazil	52	GO	5205307	Cavalcante
Brazil	52	GO	5205406	Ceres
Brazil	52	GO	5205455	Cezarina
Brazil	52	GO	5205471	Chapadão do Céu
Brazil	52	GO	5205497	Cidade Ocidental
Brazil	52	GO	5205513	Cocalzinho de Goiás
Brazil	52	GO	5205521	Colinas do Sul
Brazil	52	GO	5205703	Córrego do Ouro
Brazil	52	GO	5205802	Corumbá de Goiás
Brazil	52	GO	5205901	Corumbaíba
Brazil	52	GO	5206206	Cristalina
Brazil	52	GO	5206305	Cristianópolis
Brazil	52	GO	5206404	Crixás
Brazil	52	GO	5206503	Cromínia
Brazil	52	GO	5206602	Cumari
Brazil	52	GO	5206701	Damianópolis
Brazil	52	GO	5206800	Damolândia
Brazil	52	GO	5206909	Davinópolis
Brazil	52	GO	5207105	Diorama
Brazil	52	GO	5208301	Divinópolis de Goiás
Brazil	52	GO	5207253	Doverlândia
Brazil	52	GO	5207352	Edealina
Brazil	52	GO	5207402	Edéia
Brazil	52	GO	5207501	Estrela do Norte
Brazil	52	GO	5207535	Faina
Brazil	52	GO	5207600	Fazenda Nova
Brazil	52	GO	5207808	Firminópolis
Brazil	52	GO	5207907	Flores de Goiás
Brazil	52	GO	5208004	Formosa
Brazil	52	GO	5208103	Formoso
Brazil	52	GO	5208152	Gameleira de Goiás
Brazil	52	GO	5208400	Goianápolis
Brazil	52	GO	5208509	Goiandira
Brazil	52	GO	5208608	Goianésia
Brazil	52	GO	5208707	Goiânia
Brazil	52	GO	5208806	Goianira
Brazil	52	GO	5208905	Goiás
Brazil	52	GO	5209101	Goiatuba
Brazil	52	GO	5209150	Gouvelândia
Brazil	52	GO	5209200	Guapó
Brazil	52	GO	5209291	Guaraíta
Brazil	52	GO	5209408	Guarani de Goiás
Brazil	52	GO	5209457	Guarinos
Brazil	52	GO	5209606	Heitoraí
Brazil	52	GO	5209705	Hidrolândia
Brazil	52	GO	5209804	Hidrolina
Brazil	52	GO	5209903	Iaciara
Brazil	52	GO	5209937	Inaciolândia
Brazil	52	GO	5209952	Indiara
Brazil	52	GO	5210000	Inhumas
Brazil	52	GO	5210109	Ipameri
Brazil	52	GO	5210158	Ipiranga de Goiás
Brazil	52	GO	5210208	Iporá
Brazil	52	GO	5210307	Israelândia
Brazil	52	GO	5210406	Itaberaí
Brazil	52	GO	5210562	Itaguari
Brazil	52	GO	5210604	Itaguaru
Brazil	52	GO	5210802	Itajá
Brazil	52	GO	5210901	Itapaci
Brazil	52	GO	5211008	Itapirapuã
Brazil	52	GO	5211206	Itapuranga
Brazil	52	GO	5211305	Itarumã
Brazil	52	GO	5211404	Itauçu
Brazil	52	GO	5211503	Itumbiara
Brazil	52	GO	5211602	Ivolândia
Brazil	52	GO	5211701	Jandaia
Brazil	52	GO	5211800	Jaraguá
Brazil	52	GO	5211909	Jataí
Brazil	52	GO	5212006	Jaupaci
Brazil	52	GO	5212055	Jesúpolis
Brazil	52	GO	5212105	Joviânia
Brazil	52	GO	5212204	Jussara
Brazil	52	GO	5212253	Lagoa Santa
Brazil	52	GO	5212303	Leopoldo de Bulhões
Brazil	52	GO	5212501	Luziânia
Brazil	52	GO	5212600	Mairipotaba
Brazil	52	GO	5212709	Mambaí
Brazil	52	GO	5212808	Mara Rosa
Brazil	52	GO	5212907	Marzagão
Brazil	52	GO	5212956	Matrinchã
Brazil	52	GO	5213004	Maurilândia
Brazil	52	GO	5213053	Mimoso de Goiás
Brazil	52	GO	5213087	Minaçu
Brazil	52	GO	5213103	Mineiros
Brazil	52	GO	5213400	Moiporá
Brazil	52	GO	5213509	Monte Alegre de Goiás
Brazil	52	GO	5213707	Montes Claros de Goiás
Brazil	52	GO	5213756	Montividiu
Brazil	52	GO	5213772	Montividiu do Norte
Brazil	52	GO	5213806	Morrinhos
Brazil	52	GO	5213855	Morro Agudo de Goiás
Brazil	52	GO	5213905	Mossâmedes
Brazil	52	GO	5214002	Mozarlândia
Brazil	52	GO	5214051	Mundo Novo
Brazil	52	GO	5214101	Mutunópolis
Brazil	52	GO	5214408	Nazário
Brazil	52	GO	5214507	Nerópolis
Brazil	52	GO	5214606	Niquelândia
Brazil	52	GO	5214705	Nova América
Brazil	52	GO	5214804	Nova Aurora
Brazil	52	GO	5214838	Nova Crixás
Brazil	52	GO	5214861	Nova Glória
Brazil	52	GO	5214879	Nova Iguaçu de Goiás
Brazil	52	GO	5214903	Nova Roma
Brazil	52	GO	5215009	Nova Veneza
Brazil	52	GO	5215207	Novo Brasil
Brazil	52	GO	5215231	Novo Gama
Brazil	52	GO	5215256	Novo Planalto
Brazil	52	GO	5215306	Orizona
Brazil	52	GO	5215405	Ouro Verde de Goiás
Brazil	52	GO	5215504	Ouvidor
Brazil	52	GO	5215603	Padre Bernardo
Brazil	52	GO	5215652	Palestina de Goiás
Brazil	52	GO	5215702	Palmeiras de Goiás
Brazil	52	GO	5215801	Palmelo
Brazil	52	GO	5215900	Palminópolis
Brazil	52	GO	5216007	Panamá
Brazil	52	GO	5216304	Paranaiguara
Brazil	52	GO	5216403	Paraúna
Brazil	52	GO	5216452	Perolândia
Brazil	52	GO	5216809	Petrolina de Goiás
Brazil	52	GO	5216908	Pilar de Goiás
Brazil	52	GO	5217104	Piracanjuba
Brazil	52	GO	5217203	Piranhas
Brazil	52	GO	5217302	Pirenópolis
Brazil	52	GO	5217401	Pires do Rio
Brazil	52	GO	5217609	Planaltina
Brazil	52	GO	5217708	Pontalina
Brazil	52	GO	5218003	Porangatu
Brazil	52	GO	5218052	Porteirão
Brazil	52	GO	5218102	Portelândia
Brazil	52	GO	5218300	Posse
Brazil	52	GO	5218391	Professor Jamil
Brazil	52	GO	5218508	Quirinópolis
Brazil	52	GO	5218607	Rialma
Brazil	52	GO	5218706	Rianápolis
Brazil	52	GO	5218789	Rio Quente
Brazil	52	GO	5218805	Rio Verde
Brazil	52	GO	5218904	Rubiataba
Brazil	52	GO	5219001	Sanclerlândia
Brazil	52	GO	5219100	Santa Bárbara de Goiás
Brazil	52	GO	5219209	Santa Cruz de Goiás
Brazil	52	GO	5219258	Santa Fé de Goiás
Brazil	52	GO	5219308	Santa Helena de Goiás
Brazil	52	GO	5219357	Santa Isabel
Brazil	52	GO	5219407	Santa Rita do Araguaia
Brazil	52	GO	5219456	Santa Rita do Novo Destino
Brazil	52	GO	5219506	Santa Rosa de Goiás
Brazil	52	GO	5219605	Santa Tereza de Goiás
Brazil	52	GO	5219704	Santa Terezinha de Goiás
Brazil	52	GO	5219712	Santo Antônio da Barra
Brazil	52	GO	5219738	Santo Antônio de Goiás
Brazil	52	GO	5219753	Santo Antônio do Descoberto
Brazil	52	GO	5219803	São Domingos
Brazil	52	GO	5219902	São Francisco de Goiás
Brazil	52	GO	5220058	São João da Paraúna
Brazil	52	GO	5220009	São João d'Aliança
Brazil	52	GO	5220108	São Luís de Montes Belos
Brazil	52	GO	5220157	São Luíz do Norte
Brazil	52	GO	5220207	São Miguel do Araguaia
Brazil	52	GO	5220264	São Miguel do Passa Quatro
Brazil	52	GO	5220280	São Patrício
Brazil	52	GO	5220405	São Simão
Brazil	52	GO	5220454	Senador Canedo
Brazil	52	GO	5220504	Serranópolis
Brazil	52	GO	5220603	Silvânia
Brazil	52	GO	5220686	Simolândia
Brazil	52	GO	5220702	Sítio d'Abadia
Brazil	52	GO	5221007	Taquaral de Goiás
Brazil	52	GO	5221080	Teresina de Goiás
Brazil	52	GO	5221197	Terezópolis de Goiás
Brazil	52	GO	5221304	Três Ranchos
Brazil	52	GO	5221403	Trindade
Brazil	52	GO	5221452	Trombas
Brazil	52	GO	5221502	Turvânia
Brazil	52	GO	5221551	Turvelândia
Brazil	52	GO	5221577	Uirapuru
Brazil	52	GO	5221601	Uruaçu
Brazil	52	GO	5221700	Uruana
Brazil	52	GO	5221809	Urutaí
Brazil	52	GO	5221858	Valparaíso de Goiás
Brazil	52	GO	5221908	Varjão
Brazil	52	GO	5222005	Vianópolis
Brazil	52	GO	5222054	Vicentinópolis
Brazil	52	GO	5222203	Vila Boa
Brazil	52	GO	5222302	Vila Propício
Brazil	42	SC	4200051	Abdon Batista
Brazil	42	SC	4200101	Abelardo Luz
Brazil	42	SC	4200200	Agrolândia
Brazil	42	SC	4200309	Agronômica
Brazil	42	SC	4200408	Água Doce
Brazil	42	SC	4200507	Águas de Chapecó
Brazil	42	SC	4200556	Águas Frias
Brazil	42	SC	4200606	Águas Mornas
Brazil	42	SC	4200705	Alfredo Wagner
Brazil	42	SC	4200754	Alto Bela Vista
Brazil	42	SC	4200804	Anchieta
Brazil	42	SC	4200903	Angelina
Brazil	42	SC	4201000	Anita Garibaldi
Brazil	42	SC	4201109	Anitápolis
Brazil	42	SC	4201208	Antônio Carlos
Brazil	42	SC	4201257	Apiúna
Brazil	42	SC	4201273	Arabutã
Brazil	42	SC	4201307	Araquari
Brazil	42	SC	4201406	Araranguá
Brazil	42	SC	4201505	Armazém
Brazil	42	SC	4201604	Arroio Trinta
Brazil	42	SC	4201653	Arvoredo
Brazil	42	SC	4201703	Ascurra
Brazil	42	SC	4201802	Atalanta
Brazil	42	SC	4201901	Aurora
Brazil	42	SC	4201950	Balneário Arroio do Silva
Brazil	42	SC	4202057	Balneário Barra do Sul
Brazil	42	SC	4202008	Balneário Camboriú
Brazil	42	SC	4202073	Balneário Gaivota
Brazil	42	SC	4212809	Balneário Piçarras
Brazil	42	SC	4202081	Bandeirante
Brazil	42	SC	4202099	Barra Bonita
Brazil	42	SC	4202107	Barra Velha
Brazil	42	SC	4202131	Bela Vista do Toldo
Brazil	42	SC	4202156	Belmonte
Brazil	42	SC	4202206	Benedito Novo
Brazil	42	SC	4202305	Biguaçu
Brazil	42	SC	4202404	Blumenau
Brazil	42	SC	4202438	Bocaina do Sul
Brazil	42	SC	4202503	Bom Jardim da Serra
Brazil	42	SC	4202537	Bom Jesus
Brazil	42	SC	4202578	Bom Jesus do Oeste
Brazil	42	SC	4202602	Bom Retiro
Brazil	42	SC	4202453	Bombinhas
Brazil	42	SC	4202701	Botuverá
Brazil	42	SC	4202800	Braço do Norte
Brazil	42	SC	4202859	Braço do Trombudo
Brazil	42	SC	4202875	Brunópolis
Brazil	42	SC	4202909	Brusque
Brazil	42	SC	4203006	Caçador
Brazil	42	SC	4203105	Caibi
Brazil	42	SC	4203154	Calmon
Brazil	42	SC	4203204	Camboriú
Brazil	42	SC	4203303	Campo Alegre
Brazil	42	SC	4203402	Campo Belo do Sul
Brazil	42	SC	4203501	Campo Erê
Brazil	42	SC	4203600	Campos Novos
Brazil	42	SC	4203709	Canelinha
Brazil	42	SC	4203808	Canoinhas
Brazil	42	SC	4203253	Capão Alto
Brazil	42	SC	4203907	Capinzal
Brazil	42	SC	4203956	Capivari de Baixo
Brazil	42	SC	4204004	Catanduvas
Brazil	42	SC	4204103	Caxambu do Sul
Brazil	42	SC	4204152	Celso Ramos
Brazil	42	SC	4204178	Cerro Negro
Brazil	42	SC	4204194	Chapadão do Lageado
Brazil	42	SC	4204202	Chapecó
Brazil	42	SC	4204251	Cocal do Sul
Brazil	42	SC	4204301	Concórdia
Brazil	42	SC	4204350	Cordilheira Alta
Brazil	42	SC	4204400	Coronel Freitas
Brazil	42	SC	4204459	Coronel Martins
Brazil	42	SC	4204558	Correia Pinto
Brazil	42	SC	4204509	Corupá
Brazil	42	SC	4204608	Criciúma
Brazil	42	SC	4204707	Cunha Porã
Brazil	42	SC	4204756	Cunhataí
Brazil	42	SC	4204806	Curitibanos
Brazil	42	SC	4204905	Descanso
Brazil	42	SC	4205001	Dionísio Cerqueira
Brazil	42	SC	4205100	Dona Emma
Brazil	42	SC	4205159	Doutor Pedrinho
Brazil	42	SC	4205175	Entre Rios
Brazil	42	SC	4205191	Ermo
Brazil	42	SC	4205209	Erval Velho
Brazil	42	SC	4205308	Faxinal dos Guedes
Brazil	42	SC	4205357	Flor do Sertão
Brazil	42	SC	4205407	Florianópolis
Brazil	42	SC	4205431	Formosa do Sul
Brazil	42	SC	4205456	Forquilhinha
Brazil	42	SC	4205506	Fraiburgo
Brazil	42	SC	4205555	Frei Rogério
Brazil	42	SC	4205605	Galvão
Brazil	42	SC	4205704	Garopaba
Brazil	42	SC	4205803	Garuva
Brazil	42	SC	4205902	Gaspar
Brazil	42	SC	4206009	Governador Celso Ramos
Brazil	42	SC	4206108	Grão Pará
Brazil	42	SC	4206207	Gravatal
Brazil	42	SC	4206306	Guabiruba
Brazil	42	SC	4206405	Guaraciaba
Brazil	42	SC	4206504	Guaramirim
Brazil	42	SC	4206603	Guarujá do Sul
Brazil	42	SC	4206652	Guatambú
Brazil	42	SC	4206702	Herval d'Oeste
Brazil	42	SC	4206751	Ibiam
Brazil	42	SC	4206801	Ibicaré
Brazil	42	SC	4206900	Ibirama
Brazil	42	SC	4207007	Içara
Brazil	42	SC	4207106	Ilhota
Brazil	42	SC	4207205	Imaruí
Brazil	42	SC	4207304	Imbituba
Brazil	42	SC	4207403	Imbuia
Brazil	42	SC	4207502	Indaial
Brazil	42	SC	4207577	Iomerê
Brazil	42	SC	4207601	Ipira
Brazil	42	SC	4207650	Iporã do Oeste
Brazil	42	SC	4207684	Ipuaçu
Brazil	42	SC	4207700	Ipumirim
Brazil	42	SC	4207759	Iraceminha
Brazil	42	SC	4207809	Irani
Brazil	42	SC	4207858	Irati
Brazil	42	SC	4207908	Irineópolis
Brazil	42	SC	4208005	Itá
Brazil	42	SC	4208104	Itaiópolis
Brazil	42	SC	4208203	Itajaí
Brazil	42	SC	4208302	Itapema
Brazil	42	SC	4208401	Itapiranga
Brazil	42	SC	4208450	Itapoá
Brazil	42	SC	4208500	Ituporanga
Brazil	42	SC	4208609	Jaborá
Brazil	42	SC	4208708	Jacinto Machado
Brazil	42	SC	4208807	Jaguaruna
Brazil	42	SC	4208906	Jaraguá do Sul
Brazil	42	SC	4208955	Jardinópolis
Brazil	42	SC	4209003	Joaçaba
Brazil	42	SC	4209102	Joinville
Brazil	42	SC	4209151	José Boiteux
Brazil	42	SC	4209177	Jupiá
Brazil	42	SC	4209201	Lacerdópolis
Brazil	42	SC	4209300	Lages
Brazil	42	SC	4209409	Laguna
Brazil	42	SC	4209458	Lajeado Grande
Brazil	42	SC	4209508	Laurentino
Brazil	42	SC	4209607	Lauro Muller
Brazil	42	SC	4209706	Lebon Régis
Brazil	42	SC	4209805	Leoberto Leal
Brazil	42	SC	4209854	Lindóia do Sul
Brazil	42	SC	4209904	Lontras
Brazil	42	SC	4210001	Luiz Alves
Brazil	42	SC	4210035	Luzerna
Brazil	42	SC	4210050	Macieira
Brazil	42	SC	4210100	Mafra
Brazil	42	SC	4210209	Major Gercino
Brazil	42	SC	4210308	Major Vieira
Brazil	42	SC	4210407	Maracajá
Brazil	42	SC	4210506	Maravilha
Brazil	42	SC	4210555	Marema
Brazil	42	SC	4210605	Massaranduba
Brazil	42	SC	4210704	Matos Costa
Brazil	42	SC	4210803	Meleiro
Brazil	42	SC	4210852	Mirim Doce
Brazil	42	SC	4210902	Modelo
Brazil	42	SC	4211009	Mondaí
Brazil	42	SC	4211058	Monte Carlo
Brazil	42	SC	4211108	Monte Castelo
Brazil	42	SC	4211207	Morro da Fumaça
Brazil	42	SC	4211256	Morro Grande
Brazil	42	SC	4211306	Navegantes
Brazil	42	SC	4211405	Nova Erechim
Brazil	42	SC	4211454	Nova Itaberaba
Brazil	42	SC	4211504	Nova Trento
Brazil	42	SC	4211603	Nova Veneza
Brazil	42	SC	4211652	Novo Horizonte
Brazil	42	SC	4211702	Orleans
Brazil	42	SC	4211751	Otacílio Costa
Brazil	42	SC	4211801	Ouro
Brazil	42	SC	4211850	Ouro Verde
Brazil	42	SC	4211876	Paial
Brazil	42	SC	4211892	Painel
Brazil	42	SC	4211900	Palhoça
Brazil	42	SC	4212007	Palma Sola
Brazil	42	SC	4212056	Palmeira
Brazil	42	SC	4212106	Palmitos
Brazil	42	SC	4212205	Papanduva
Brazil	42	SC	4212239	Paraíso
Brazil	42	SC	4212254	Passo de Torres
Brazil	42	SC	4212270	Passos Maia
Brazil	42	SC	4212304	Paulo Lopes
Brazil	42	SC	4212403	Pedras Grandes
Brazil	42	SC	4212502	Penha
Brazil	42	SC	4212601	Peritiba
Brazil	42	SC	4212700	Petrolândia
Brazil	42	SC	4212908	Pinhalzinho
Brazil	42	SC	4213005	Pinheiro Preto
Brazil	42	SC	4213104	Piratuba
Brazil	42	SC	4213153	Planalto Alegre
Brazil	42	SC	4213203	Pomerode
Brazil	42	SC	4213302	Ponte Alta
Brazil	42	SC	4213351	Ponte Alta do Norte
Brazil	42	SC	4213401	Ponte Serrada
Brazil	42	SC	4213500	Porto Belo
Brazil	42	SC	4213609	Porto União
Brazil	42	SC	4213708	Pouso Redondo
Brazil	42	SC	4213807	Praia Grande
Brazil	42	SC	4213906	Presidente Castello Branco
Brazil	42	SC	4214003	Presidente Getúlio
Brazil	42	SC	4214102	Presidente Nereu
Brazil	42	SC	4214151	Princesa
Brazil	42	SC	4214201	Quilombo
Brazil	42	SC	4214300	Rancho Queimado
Brazil	42	SC	4214409	Rio das Antas
Brazil	42	SC	4214508	Rio do Campo
Brazil	42	SC	4214607	Rio do Oeste
Brazil	42	SC	4214805	Rio do Sul
Brazil	42	SC	4214706	Rio dos Cedros
Brazil	42	SC	4214904	Rio Fortuna
Brazil	42	SC	4215000	Rio Negrinho
Brazil	42	SC	4215059	Rio Rufino
Brazil	42	SC	4215075	Riqueza
Brazil	42	SC	4215109	Rodeio
Brazil	42	SC	4215208	Romelândia
Brazil	42	SC	4215307	Salete
Brazil	42	SC	4215356	Saltinho
Brazil	42	SC	4215406	Salto Veloso
Brazil	42	SC	4215455	Sangão
Brazil	42	SC	4215505	Santa Cecília
Brazil	42	SC	4215554	Santa Helena
Brazil	42	SC	4215604	Santa Rosa de Lima
Brazil	42	SC	4215653	Santa Rosa do Sul
Brazil	42	SC	4215679	Santa Terezinha
Brazil	42	SC	4215687	Santa Terezinha do Progresso
Brazil	42	SC	4215695	Santiago do Sul
Brazil	42	SC	4215703	Santo Amaro da Imperatriz
Brazil	42	SC	4215802	São Bento do Sul
Brazil	42	SC	4215752	São Bernardino
Brazil	42	SC	4215901	São Bonifácio
Brazil	42	SC	4216008	São Carlos
Brazil	42	SC	4216057	São Cristovão do Sul
Brazil	42	SC	4216107	São Domingos
Brazil	42	SC	4216206	São Francisco do Sul
Brazil	42	SC	4216305	São João Batista
Brazil	42	SC	4216354	São João do Itaperiú
Brazil	42	SC	4216255	São João do Oeste
Brazil	42	SC	4216404	São João do Sul
Brazil	42	SC	4216503	São Joaquim
Brazil	42	SC	4216602	São José
Brazil	42	SC	4216701	São José do Cedro
Brazil	42	SC	4216800	São José do Cerrito
Brazil	42	SC	4216909	São Lourenço do Oeste
Brazil	42	SC	4217006	São Ludgero
Brazil	42	SC	4217105	São Martinho
Brazil	42	SC	4217154	São Miguel da Boa Vista
Brazil	42	SC	4217204	São Miguel do Oeste
Brazil	42	SC	4217253	São Pedro de Alcântara
Brazil	42	SC	4217303	Saudades
Brazil	42	SC	4217402	Schroeder
Brazil	42	SC	4217501	Seara
Brazil	42	SC	4217550	Serra Alta
Brazil	42	SC	4217600	Siderópolis
Brazil	42	SC	4217709	Sombrio
Brazil	42	SC	4217758	Sul Brasil
Brazil	42	SC	4217808	Taió
Brazil	42	SC	4217907	Tangará
Brazil	42	SC	4217956	Tigrinhos
Brazil	42	SC	4218004	Tijucas
Brazil	42	SC	4218103	Timbé do Sul
Brazil	42	SC	4218202	Timbó
Brazil	42	SC	4218251	Timbó Grande
Brazil	42	SC	4218301	Três Barras
Brazil	42	SC	4218350	Treviso
Brazil	42	SC	4218400	Treze de Maio
Brazil	42	SC	4218509	Treze Tílias
Brazil	42	SC	4218608	Trombudo Central
Brazil	42	SC	4218707	Tubarão
Brazil	42	SC	4218756	Tunápolis
Brazil	42	SC	4218806	Turvo
Brazil	42	SC	4218855	União do Oeste
Brazil	42	SC	4218905	Urubici
Brazil	42	SC	4218954	Urupema
Brazil	42	SC	4219002	Urussanga
Brazil	42	SC	4219101	Vargeão
Brazil	42	SC	4219150	Vargem
Brazil	42	SC	4219176	Vargem Bonita
Brazil	42	SC	4219200	Vidal Ramos
Brazil	42	SC	4219309	Videira
Brazil	42	SC	4219358	Vitor Meireles
Brazil	42	SC	4219408	Witmarsum
Brazil	42	SC	4219507	Xanxerê
Brazil	42	SC	4219606	Xavantina
Brazil	42	SC	4219705	Xaxim
Brazil	42	SC	4219853	Zortéa
Brazil	41	PR	4100103	Abatiá
Brazil	41	PR	4100202	Adrianópolis
Brazil	41	PR	4100301	Agudos do Sul
Brazil	41	PR	4100400	Almirante Tamandaré
Brazil	41	PR	4100459	Altamira do Paraná
Brazil	41	PR	4128625	Alto Paraíso
Brazil	41	PR	4100608	Alto Paraná
Brazil	41	PR	4100707	Alto Piquiri
Brazil	41	PR	4100509	Altônia
Brazil	41	PR	4100806	Alvorada do Sul
Brazil	41	PR	4100905	Amaporã
Brazil	41	PR	4101002	Ampére
Brazil	41	PR	4101051	Anahy
Brazil	41	PR	4101101	Andirá
Brazil	41	PR	4101150	Ângulo
Brazil	41	PR	4101200	Antonina
Brazil	41	PR	4101309	Antônio Olinto
Brazil	41	PR	4101408	Apucarana
Brazil	41	PR	4101507	Arapongas
Brazil	41	PR	4101606	Arapoti
Brazil	41	PR	4101655	Arapuã
Brazil	41	PR	4101705	Araruna
Brazil	41	PR	4101804	Araucária
Brazil	41	PR	4101853	Ariranha do Ivaí
Brazil	41	PR	4101903	Assaí
Brazil	41	PR	4102000	Assis Chateaubriand
Brazil	41	PR	4102109	Astorga
Brazil	41	PR	4102208	Atalaia
Brazil	41	PR	4102307	Balsa Nova
Brazil	41	PR	4102406	Bandeirantes
Brazil	41	PR	4102505	Barbosa Ferraz
Brazil	41	PR	4102703	Barra do Jacaré
Brazil	41	PR	4102604	Barracão
Brazil	41	PR	4102752	Bela Vista da Caroba
Brazil	41	PR	4102802	Bela Vista do Paraíso
Brazil	41	PR	4102901	Bituruna
Brazil	41	PR	4103008	Boa Esperança
Brazil	41	PR	4103024	Boa Esperança do Iguaçu
Brazil	41	PR	4103040	Boa Ventura de São Roque
Brazil	41	PR	4103057	Boa Vista da Aparecida
Brazil	41	PR	4103107	Bocaiúva do Sul
Brazil	41	PR	4103156	Bom Jesus do Sul
Brazil	41	PR	4103206	Bom Sucesso
Brazil	41	PR	4103222	Bom Sucesso do Sul
Brazil	41	PR	4103305	Borrazópolis
Brazil	41	PR	4103354	Braganey
Brazil	41	PR	4103370	Brasilândia do Sul
Brazil	41	PR	4103404	Cafeara
Brazil	41	PR	4103453	Cafelândia
Brazil	41	PR	4103479	Cafezal do Sul
Brazil	41	PR	4103503	Califórnia
Brazil	41	PR	4103602	Cambará
Brazil	41	PR	4103701	Cambé
Brazil	41	PR	4103800	Cambira
Brazil	41	PR	4103909	Campina da Lagoa
Brazil	41	PR	4103958	Campina do Simão
Brazil	41	PR	4104006	Campina Grande do Sul
Brazil	41	PR	4104055	Campo Bonito
Brazil	41	PR	4104105	Campo do Tenente
Brazil	41	PR	4104204	Campo Largo
Brazil	41	PR	4104253	Campo Magro
Brazil	41	PR	4104303	Campo Mourão
Brazil	41	PR	4104402	Cândido de Abreu
Brazil	41	PR	4104428	Candói
Brazil	41	PR	4104451	Cantagalo
Brazil	41	PR	4104501	Capanema
Brazil	41	PR	4104600	Capitão Leônidas Marques
Brazil	41	PR	4104659	Carambeí
Brazil	41	PR	4104709	Carlópolis
Brazil	41	PR	4104808	Cascavel
Brazil	41	PR	4104907	Castro
Brazil	41	PR	4105003	Catanduvas
Brazil	41	PR	4105102	Centenário do Sul
Brazil	41	PR	4105201	Cerro Azul
Brazil	41	PR	4105300	Céu Azul
Brazil	41	PR	4105409	Chopinzinho
Brazil	41	PR	4105508	Cianorte
Brazil	41	PR	4105607	Cidade Gaúcha
Brazil	41	PR	4105706	Clevelândia
Brazil	41	PR	4105805	Colombo
Brazil	41	PR	4105904	Colorado
Brazil	41	PR	4106001	Congonhinhas
Brazil	41	PR	4106100	Conselheiro Mairinck
Brazil	41	PR	4106209	Contenda
Brazil	41	PR	4106308	Corbélia
Brazil	41	PR	4106407	Cornélio Procópio
Brazil	41	PR	4106456	Coronel Domingos Soares
Brazil	41	PR	4106506	Coronel Vivida
Brazil	41	PR	4106555	Corumbataí do Sul
Brazil	41	PR	4106803	Cruz Machado
Brazil	41	PR	4106571	Cruzeiro do Iguaçu
Brazil	41	PR	4106605	Cruzeiro do Oeste
Brazil	41	PR	4106704	Cruzeiro do Sul
Brazil	41	PR	4106852	Cruzmaltina
Brazil	41	PR	4106902	Curitiba
Brazil	41	PR	4107009	Curiúva
Brazil	41	PR	4107108	Diamante do Norte
Brazil	41	PR	4107124	Diamante do Sul
Brazil	41	PR	4107157	Diamante D'Oeste
Brazil	41	PR	4107207	Dois Vizinhos
Brazil	41	PR	4107256	Douradina
Brazil	41	PR	4107306	Doutor Camargo
Brazil	41	PR	4128633	Doutor Ulysses
Brazil	41	PR	4107405	Enéas Marques
Brazil	41	PR	4107504	Engenheiro Beltrão
Brazil	41	PR	4107538	Entre Rios do Oeste
Brazil	41	PR	4107520	Esperança Nova
Brazil	41	PR	4107546	Espigão Alto do Iguaçu
Brazil	41	PR	4107553	Farol
Brazil	41	PR	4107603	Faxinal
Brazil	41	PR	4107652	Fazenda Rio Grande
Brazil	41	PR	4107702	Fênix
Brazil	41	PR	4107736	Fernandes Pinheiro
Brazil	41	PR	4107751	Figueira
Brazil	41	PR	4107850	Flor da Serra do Sul
Brazil	41	PR	4107801	Floraí
Brazil	41	PR	4107900	Floresta
Brazil	41	PR	4108007	Florestópolis
Brazil	41	PR	4108106	Flórida
Brazil	41	PR	4108205	Formosa do Oeste
Brazil	41	PR	4108304	Foz do Iguaçu
Brazil	41	PR	4108452	Foz do Jordão
Brazil	41	PR	4108320	Francisco Alves
Brazil	41	PR	4108403	Francisco Beltrão
Brazil	41	PR	4108502	General Carneiro
Brazil	41	PR	4108551	Godoy Moreira
Brazil	41	PR	4108601	Goioerê
Brazil	41	PR	4108650	Goioxim
Brazil	41	PR	4108700	Grandes Rios
Brazil	41	PR	4108809	Guaíra
Brazil	41	PR	4108908	Guairaçá
Brazil	41	PR	4108957	Guamiranga
Brazil	41	PR	4109005	Guapirama
Brazil	41	PR	4109104	Guaporema
Brazil	41	PR	4109203	Guaraci
Brazil	41	PR	4109302	Guaraniaçu
Brazil	41	PR	4109401	Guarapuava
Brazil	41	PR	4109500	Guaraqueçaba
Brazil	41	PR	4109609	Guaratuba
Brazil	41	PR	4109658	Honório Serpa
Brazil	41	PR	4109708	Ibaiti
Brazil	41	PR	4109757	Ibema
Brazil	41	PR	4109807	Ibiporã
Brazil	41	PR	4109906	Icaraíma
Brazil	41	PR	4110003	Iguaraçu
Brazil	41	PR	4110052	Iguatu
Brazil	41	PR	4110078	Imbaú
Brazil	41	PR	4110102	Imbituva
Brazil	41	PR	4110201	Inácio Martins
Brazil	41	PR	4110300	Inajá
Brazil	41	PR	4110409	Indianópolis
Brazil	41	PR	4110508	Ipiranga
Brazil	41	PR	4110607	Iporã
Brazil	41	PR	4110656	Iracema do Oeste
Brazil	41	PR	4110706	Irati
Brazil	41	PR	4110805	Iretama
Brazil	41	PR	4110904	Itaguajé
Brazil	41	PR	4110953	Itaipulândia
Brazil	41	PR	4111001	Itambaracá
Brazil	41	PR	4111100	Itambé
Brazil	41	PR	4111209	Itapejara d'Oeste
Brazil	41	PR	4111258	Itaperuçu
Brazil	41	PR	4111308	Itaúna do Sul
Brazil	41	PR	4111407	Ivaí
Brazil	41	PR	4111506	Ivaiporã
Brazil	41	PR	4111555	Ivaté
Brazil	41	PR	4111605	Ivatuba
Brazil	41	PR	4111704	Jaboti
Brazil	41	PR	4111803	Jacarezinho
Brazil	41	PR	4111902	Jaguapitã
Brazil	41	PR	4112009	Jaguariaíva
Brazil	41	PR	4112108	Jandaia do Sul
Brazil	41	PR	4112207	Janiópolis
Brazil	41	PR	4112306	Japira
Brazil	41	PR	4112405	Japurá
Brazil	41	PR	4112504	Jardim Alegre
Brazil	41	PR	4112603	Jardim Olinda
Brazil	41	PR	4112702	Jataizinho
Brazil	41	PR	4112751	Jesuítas
Brazil	41	PR	4112801	Joaquim Távora
Brazil	41	PR	4112900	Jundiaí do Sul
Brazil	41	PR	4112959	Juranda
Brazil	41	PR	4113007	Jussara
Brazil	41	PR	4113106	Kaloré
Brazil	41	PR	4113205	Lapa
Brazil	41	PR	4113254	Laranjal
Brazil	41	PR	4113304	Laranjeiras do Sul
Brazil	41	PR	4113403	Leópolis
Brazil	41	PR	4113429	Lidianópolis
Brazil	41	PR	4113452	Lindoeste
Brazil	41	PR	4113502	Loanda
Brazil	41	PR	4113601	Lobato
Brazil	41	PR	4113700	Londrina
Brazil	41	PR	4113734	Luiziana
Brazil	41	PR	4113759	Lunardelli
Brazil	41	PR	4113809	Lupionópolis
Brazil	41	PR	4113908	Mallet
Brazil	41	PR	4114005	Mamborê
Brazil	41	PR	4114104	Mandaguaçu
Brazil	41	PR	4114203	Mandaguari
Brazil	41	PR	4114302	Mandirituba
Brazil	41	PR	4114351	Manfrinópolis
Brazil	41	PR	4114401	Mangueirinha
Brazil	41	PR	4114500	Manoel Ribas
Brazil	41	PR	4114609	Marechal Cândido Rondon
Brazil	41	PR	4114708	Maria Helena
Brazil	41	PR	4114807	Marialva
Brazil	41	PR	4114906	Marilândia do Sul
Brazil	41	PR	4115002	Marilena
Brazil	41	PR	4115101	Mariluz
Brazil	41	PR	4115200	Maringá
Brazil	41	PR	4115309	Mariópolis
Brazil	41	PR	4115358	Maripá
Brazil	41	PR	4115408	Marmeleiro
Brazil	41	PR	4115457	Marquinho
Brazil	41	PR	4115507	Marumbi
Brazil	41	PR	4115606	Matelândia
Brazil	41	PR	4115705	Matinhos
Brazil	41	PR	4115739	Mato Rico
Brazil	41	PR	4115754	Mauá da Serra
Brazil	41	PR	4115804	Medianeira
Brazil	41	PR	4115853	Mercedes
Brazil	41	PR	4115903	Mirador
Brazil	41	PR	4116000	Miraselva
Brazil	41	PR	4116059	Missal
Brazil	41	PR	4116109	Moreira Sales
Brazil	41	PR	4116208	Morretes
Brazil	41	PR	4116307	Munhoz de Melo
Brazil	41	PR	4116406	Nossa Senhora das Graças
Brazil	41	PR	4116505	Nova Aliança do Ivaí
Brazil	41	PR	4116604	Nova América da Colina
Brazil	41	PR	4116703	Nova Aurora
Brazil	41	PR	4116802	Nova Cantu
Brazil	41	PR	4116901	Nova Esperança
Brazil	41	PR	4116950	Nova Esperança do Sudoeste
Brazil	41	PR	4117008	Nova Fátima
Brazil	41	PR	4117057	Nova Laranjeiras
Brazil	41	PR	4117107	Nova Londrina
Brazil	41	PR	4117206	Nova Olímpia
Brazil	41	PR	4117255	Nova Prata do Iguaçu
Brazil	41	PR	4117214	Nova Santa Bárbara
Brazil	41	PR	4117222	Nova Santa Rosa
Brazil	41	PR	4117271	Nova Tebas
Brazil	41	PR	4117297	Novo Itacolomi
Brazil	41	PR	4117305	Ortigueira
Brazil	41	PR	4117404	Ourizona
Brazil	41	PR	4117453	Ouro Verde do Oeste
Brazil	41	PR	4117503	Paiçandu
Brazil	41	PR	4117602	Palmas
Brazil	41	PR	4117701	Palmeira
Brazil	41	PR	4117800	Palmital
Brazil	41	PR	4117909	Palotina
Brazil	41	PR	4118006	Paraíso do Norte
Brazil	41	PR	4118105	Paranacity
Brazil	41	PR	4118204	Paranaguá
Brazil	41	PR	4118303	Paranapoema
Brazil	41	PR	4118402	Paranavaí
Brazil	41	PR	4118451	Pato Bragado
Brazil	41	PR	4118501	Pato Branco
Brazil	41	PR	4118600	Paula Freitas
Brazil	41	PR	4118709	Paulo Frontin
Brazil	41	PR	4118808	Peabiru
Brazil	41	PR	4118857	Perobal
Brazil	41	PR	4118907	Pérola
Brazil	41	PR	4119004	Pérola d'Oeste
Brazil	41	PR	4119103	Piên
Brazil	41	PR	4119152	Pinhais
Brazil	41	PR	4119251	Pinhal de São Bento
Brazil	41	PR	4119202	Pinhalão
Brazil	41	PR	4119301	Pinhão
Brazil	41	PR	4119400	Piraí do Sul
Brazil	41	PR	4119509	Piraquara
Brazil	41	PR	4119608	Pitanga
Brazil	41	PR	4119657	Pitangueiras
Brazil	41	PR	4119707	Planaltina do Paraná
Brazil	41	PR	4119806	Planalto
Brazil	41	PR	4119905	Ponta Grossa
Brazil	41	PR	4119954	Pontal do Paraná
Brazil	41	PR	4120002	Porecatu
Brazil	41	PR	4120101	Porto Amazonas
Brazil	41	PR	4120150	Porto Barreiro
Brazil	41	PR	4120200	Porto Rico
Brazil	41	PR	4120309	Porto Vitória
Brazil	41	PR	4120333	Prado Ferreira
Brazil	41	PR	4120358	Pranchita
Brazil	41	PR	4120408	Presidente Castelo Branco
Brazil	41	PR	4120507	Primeiro de Maio
Brazil	41	PR	4120606	Prudentópolis
Brazil	41	PR	4120655	Quarto Centenário
Brazil	41	PR	4120705	Quatiguá
Brazil	41	PR	4120804	Quatro Barras
Brazil	41	PR	4120853	Quatro Pontes
Brazil	41	PR	4120903	Quedas do Iguaçu
Brazil	41	PR	4121000	Querência do Norte
Brazil	41	PR	4121109	Quinta do Sol
Brazil	41	PR	4121208	Quitandinha
Brazil	41	PR	4121257	Ramilândia
Brazil	41	PR	4121307	Rancho Alegre
Brazil	41	PR	4121356	Rancho Alegre D'Oeste
Brazil	41	PR	4121406	Realeza
Brazil	41	PR	4121505	Rebouças
Brazil	41	PR	4121604	Renascença
Brazil	41	PR	4121703	Reserva
Brazil	41	PR	4121752	Reserva do Iguaçu
Brazil	41	PR	4121802	Ribeirão Claro
Brazil	41	PR	4121901	Ribeirão do Pinhal
Brazil	41	PR	4122008	Rio Azul
Brazil	41	PR	4122107	Rio Bom
Brazil	41	PR	4122156	Rio Bonito do Iguaçu
Brazil	41	PR	4122172	Rio Branco do Ivaí
Brazil	41	PR	4122206	Rio Branco do Sul
Brazil	41	PR	4122305	Rio Negro
Brazil	41	PR	4122404	Rolândia
Brazil	41	PR	4122503	Roncador
Brazil	41	PR	4122602	Rondon
Brazil	41	PR	4122651	Rosário do Ivaí
Brazil	41	PR	4122701	Sabáudia
Brazil	41	PR	4122800	Salgado Filho
Brazil	41	PR	4122909	Salto do Itararé
Brazil	41	PR	4123006	Salto do Lontra
Brazil	41	PR	4123105	Santa Amélia
Brazil	41	PR	4123204	Santa Cecília do Pavão
Brazil	41	PR	4123303	Santa Cruz de Monte Castelo
Brazil	41	PR	4123402	Santa Fé
Brazil	41	PR	4123501	Santa Helena
Brazil	41	PR	4123600	Santa Inês
Brazil	41	PR	4123709	Santa Isabel do Ivaí
Brazil	41	PR	4123808	Santa Izabel do Oeste
Brazil	41	PR	4123824	Santa Lúcia
Brazil	41	PR	4123857	Santa Maria do Oeste
Brazil	41	PR	4123907	Santa Mariana
Brazil	41	PR	4123956	Santa Mônica
Brazil	41	PR	4124020	Santa Tereza do Oeste
Brazil	41	PR	4124053	Santa Terezinha de Itaipu
Brazil	41	PR	4124004	Santana do Itararé
Brazil	41	PR	4124103	Santo Antônio da Platina
Brazil	41	PR	4124202	Santo Antônio do Caiuá
Brazil	41	PR	4124301	Santo Antônio do Paraíso
Brazil	41	PR	4124400	Santo Antônio do Sudoeste
Brazil	41	PR	4124509	Santo Inácio
Brazil	41	PR	4124608	São Carlos do Ivaí
Brazil	41	PR	4124707	São Jerônimo da Serra
Brazil	41	PR	4124806	São João
Brazil	41	PR	4124905	São João do Caiuá
Brazil	41	PR	4125001	São João do Ivaí
Brazil	41	PR	4125100	São João do Triunfo
Brazil	41	PR	4125308	São Jorge do Ivaí
Brazil	41	PR	4125357	São Jorge do Patrocínio
Brazil	41	PR	4125209	São Jorge d'Oeste
Brazil	41	PR	4125407	São José da Boa Vista
Brazil	41	PR	4125456	São José das Palmeiras
Brazil	41	PR	4125506	São José dos Pinhais
Brazil	41	PR	4125555	São Manoel do Paraná
Brazil	41	PR	4125605	São Mateus do Sul
Brazil	41	PR	4125704	São Miguel do Iguaçu
Brazil	41	PR	4125753	São Pedro do Iguaçu
Brazil	41	PR	4125803	São Pedro do Ivaí
Brazil	41	PR	4125902	São Pedro do Paraná
Brazil	41	PR	4126009	São Sebastião da Amoreira
Brazil	41	PR	4126108	São Tomé
Brazil	41	PR	4126207	Sapopema
Brazil	41	PR	4126256	Sarandi
Brazil	41	PR	4126272	Saudade do Iguaçu
Brazil	41	PR	4126306	Sengés
Brazil	41	PR	4126355	Serranópolis do Iguaçu
Brazil	41	PR	4126405	Sertaneja
Brazil	41	PR	4126504	Sertanópolis
Brazil	41	PR	4126603	Siqueira Campos
Brazil	41	PR	4126652	Sulina
Brazil	41	PR	4126678	Tamarana
Brazil	41	PR	4126702	Tamboara
Brazil	41	PR	4126801	Tapejara
Brazil	41	PR	4126900	Tapira
Brazil	41	PR	4127007	Teixeira Soares
Brazil	41	PR	4127106	Telêmaco Borba
Brazil	41	PR	4127205	Terra Boa
Brazil	41	PR	4127304	Terra Rica
Brazil	41	PR	4127403	Terra Roxa
Brazil	41	PR	4127502	Tibagi
Brazil	41	PR	4127601	Tijucas do Sul
Brazil	41	PR	4127700	Toledo
Brazil	41	PR	4127809	Tomazina
Brazil	41	PR	4127858	Três Barras do Paraná
Brazil	41	PR	4127882	Tunas do Paraná
Brazil	41	PR	4127908	Tuneiras do Oeste
Brazil	41	PR	4127957	Tupãssi
Brazil	41	PR	4127965	Turvo
Brazil	41	PR	4128005	Ubiratã
Brazil	41	PR	4128104	Umuarama
Brazil	41	PR	4128203	União da Vitória
Brazil	41	PR	4128302	Uniflor
Brazil	41	PR	4128401	Uraí
Brazil	41	PR	4128534	Ventania
Brazil	41	PR	4128559	Vera Cruz do Oeste
Brazil	41	PR	4128609	Verê
Brazil	41	PR	4128658	Virmond
Brazil	41	PR	4128708	Vitorino
Brazil	41	PR	4128500	Wenceslau Braz
Brazil	41	PR	4128807	Xambrê
Brazil	29	BA	2900108	Abaíra
Brazil	29	BA	2900207	Abaré
Brazil	29	BA	2900306	Acajutiba
Brazil	29	BA	2900355	Adustina
Brazil	29	BA	2900405	Água Fria
Brazil	29	BA	2900603	Aiquara
Brazil	29	BA	2900702	Alagoinhas
Brazil	29	BA	2900801	Alcobaça
Brazil	29	BA	2900900	Almadina
Brazil	29	BA	2901007	Amargosa
Brazil	29	BA	2901106	Amélia Rodrigues
Brazil	29	BA	2901155	América Dourada
Brazil	29	BA	2901205	Anagé
Brazil	29	BA	2901304	Andaraí
Brazil	29	BA	2901353	Andorinha
Brazil	29	BA	2901403	Angical
Brazil	29	BA	2901502	Anguera
Brazil	29	BA	2901601	Antas
Brazil	29	BA	2901700	Antônio Cardoso
Brazil	29	BA	2901809	Antônio Gonçalves
Brazil	29	BA	2901908	Aporá
Brazil	29	BA	2901957	Apuarema
Brazil	29	BA	2902054	Araças
Brazil	29	BA	2902005	Aracatu
Brazil	29	BA	2902104	Araci
Brazil	29	BA	2902203	Aramari
Brazil	29	BA	2902252	Arataca
Brazil	29	BA	2902302	Aratuípe
Brazil	29	BA	2902401	Aurelino Leal
Brazil	29	BA	2902500	Baianópolis
Brazil	29	BA	2902609	Baixa Grande
Brazil	29	BA	2902658	Banzaê
Brazil	29	BA	2902708	Barra
Brazil	29	BA	2902807	Barra da Estiva
Brazil	29	BA	2902906	Barra do Choça
Brazil	29	BA	2903003	Barra do Mendes
Brazil	29	BA	2903102	Barra do Rocha
Brazil	29	BA	2903201	Barreiras
Brazil	29	BA	2903235	Barro Alto
Brazil	29	BA	2903300	Barro Preto
Brazil	29	BA	2903276	Barrocas
Brazil	29	BA	2903409	Belmonte
Brazil	29	BA	2903508	Belo Campo
Brazil	29	BA	2903607	Biritinga
Brazil	29	BA	2903706	Boa Nova
Brazil	29	BA	2903805	Boa Vista do Tupim
Brazil	29	BA	2903904	Bom Jesus da Lapa
Brazil	29	BA	2903953	Bom Jesus da Serra
Brazil	29	BA	2904001	Boninal
Brazil	29	BA	2904050	Bonito
Brazil	29	BA	2904100	Boquira
Brazil	29	BA	2904209	Botuporã
Brazil	29	BA	2904308	Brejões
Brazil	29	BA	2904407	Brejolândia
Brazil	29	BA	2904506	Brotas de Macaúbas
Brazil	29	BA	2904605	Brumado
Brazil	29	BA	2904704	Buerarema
Brazil	29	BA	2904753	Buritirama
Brazil	29	BA	2904803	Caatiba
Brazil	29	BA	2904852	Cabaceiras do Paraguaçu
Brazil	29	BA	2904902	Cachoeira
Brazil	29	BA	2905008	Caculé
Brazil	29	BA	2905107	Caém
Brazil	29	BA	2905156	Caetanos
Brazil	29	BA	2905206	Caetité
Brazil	29	BA	2905305	Cafarnaum
Brazil	29	BA	2905404	Cairu
Brazil	29	BA	2905503	Caldeirão Grande
Brazil	29	BA	2905602	Camacan
Brazil	29	BA	2905701	Camaçari
Brazil	29	BA	2905800	Camamu
Brazil	29	BA	2905909	Campo Alegre de Lourdes
Brazil	29	BA	2906006	Campo Formoso
Brazil	29	BA	2906105	Canápolis
Brazil	29	BA	2906204	Canarana
Brazil	29	BA	2906303	Canavieiras
Brazil	29	BA	2906402	Candeal
Brazil	29	BA	2906501	Candeias
Brazil	29	BA	2906600	Candiba
Brazil	29	BA	2906709	Cândido Sales
Brazil	29	BA	2906808	Cansanção
Brazil	29	BA	2906824	Canudos
Brazil	29	BA	2906857	Capela do Alto Alegre
Brazil	29	BA	2906873	Capim Grosso
Brazil	29	BA	2906899	Caraíbas
Brazil	29	BA	2906907	Caravelas
Brazil	29	BA	2907004	Cardeal da Silva
Brazil	29	BA	2907103	Carinhanha
Brazil	29	BA	2907202	Casa Nova
Brazil	29	BA	2907301	Castro Alves
Brazil	29	BA	2907400	Catolândia
Brazil	29	BA	2907509	Catu
Brazil	29	BA	2907558	Caturama
Brazil	29	BA	2907608	Central
Brazil	29	BA	2907707	Chorrochó
Brazil	29	BA	2907806	Cícero Dantas
Brazil	29	BA	2907905	Cipó
Brazil	29	BA	2908002	Coaraci
Brazil	29	BA	2908101	Cocos
Brazil	29	BA	2908200	Conceição da Feira
Brazil	29	BA	2908309	Conceição do Almeida
Brazil	29	BA	2908408	Conceição do Coité
Brazil	29	BA	2908507	Conceição do Jacuípe
Brazil	29	BA	2908606	Conde
Brazil	29	BA	2908705	Condeúba
Brazil	29	BA	2908804	Contendas do Sincorá
Brazil	29	BA	2908903	Coração de Maria
Brazil	29	BA	2909000	Cordeiros
Brazil	29	BA	2909109	Coribe
Brazil	29	BA	2909208	Coronel João Sá
Brazil	29	BA	2909307	Correntina
Brazil	29	BA	2909406	Cotegipe
Brazil	29	BA	2909505	Cravolândia
Brazil	29	BA	2909604	Crisópolis
Brazil	29	BA	2909703	Cristópolis
Brazil	29	BA	2909802	Cruz das Almas
Brazil	29	BA	2909901	Curaçá
Brazil	29	BA	2910008	Dário Meira
Brazil	29	BA	2910057	Dias d'Ávila
Brazil	29	BA	2910107	Dom Basílio
Brazil	29	BA	2910206	Dom Macedo Costa
Brazil	29	BA	2910305	Elísio Medrado
Brazil	29	BA	2910404	Encruzilhada
Brazil	29	BA	2910503	Entre Rios
Brazil	29	BA	2900504	Érico Cardoso
Brazil	29	BA	2910602	Esplanada
Brazil	29	BA	2910701	Euclides da Cunha
Brazil	29	BA	2910727	Eunápolis
Brazil	29	BA	2910750	Fátima
Brazil	29	BA	2910776	Feira da Mata
Brazil	29	BA	2910800	Feira de Santana
Brazil	29	BA	2910859	Filadélfia
Brazil	29	BA	2910909	Firmino Alves
Brazil	29	BA	2911006	Floresta Azul
Brazil	29	BA	2911105	Formosa do Rio Preto
Brazil	29	BA	2911204	Gandu
Brazil	29	BA	2911253	Gavião
Brazil	29	BA	2911303	Gentio do Ouro
Brazil	29	BA	2911402	Glória
Brazil	29	BA	2911501	Gongogi
Brazil	29	BA	2911600	Governador Mangabeira
Brazil	29	BA	2911659	Guajeru
Brazil	29	BA	2911709	Guanambi
Brazil	29	BA	2911808	Guaratinga
Brazil	29	BA	2911857	Heliópolis
Brazil	29	BA	2911907	Iaçu
Brazil	29	BA	2912004	Ibiassucê
Brazil	29	BA	2912103	Ibicaraí
Brazil	29	BA	2912202	Ibicoara
Brazil	29	BA	2912301	Ibicuí
Brazil	29	BA	2912400	Ibipeba
Brazil	29	BA	2912509	Ibipitanga
Brazil	29	BA	2912608	Ibiquera
Brazil	29	BA	2912707	Ibirapitanga
Brazil	29	BA	2912806	Ibirapuã
Brazil	29	BA	2912905	Ibirataia
Brazil	29	BA	2913002	Ibitiara
Brazil	29	BA	2913101	Ibititá
Brazil	29	BA	2913200	Ibotirama
Brazil	29	BA	2913309	Ichu
Brazil	29	BA	2913408	Igaporã
Brazil	29	BA	2913457	Igrapiúna
Brazil	29	BA	2913507	Iguaí
Brazil	29	BA	2913606	Ilhéus
Brazil	29	BA	2913705	Inhambupe
Brazil	29	BA	2913804	Ipecaetá
Brazil	29	BA	2913903	Ipiaú
Brazil	29	BA	2914000	Ipirá
Brazil	29	BA	2914109	Ipupiara
Brazil	29	BA	2914208	Irajuba
Brazil	29	BA	2914307	Iramaia
Brazil	29	BA	2914406	Iraquara
Brazil	29	BA	2914505	Irará
Brazil	29	BA	2914604	Irecê
Brazil	29	BA	2914653	Itabela
Brazil	29	BA	2914703	Itaberaba
Brazil	29	BA	2914802	Itabuna
Brazil	29	BA	2914901	Itacaré
Brazil	29	BA	2915007	Itaeté
Brazil	29	BA	2915106	Itagi
Brazil	29	BA	2915205	Itagibá
Brazil	29	BA	2915304	Itagimirim
Brazil	29	BA	2915353	Itaguaçu da Bahia
Brazil	29	BA	2915403	Itaju do Colônia
Brazil	29	BA	2915502	Itajuípe
Brazil	29	BA	2915601	Itamaraju
Brazil	29	BA	2915700	Itamari
Brazil	29	BA	2915809	Itambé
Brazil	29	BA	2915908	Itanagra
Brazil	29	BA	2916005	Itanhém
Brazil	29	BA	2916104	Itaparica
Brazil	29	BA	2916203	Itapé
Brazil	29	BA	2916302	Itapebi
Brazil	29	BA	2916401	Itapetinga
Brazil	29	BA	2916500	Itapicuru
Brazil	29	BA	2916609	Itapitanga
Brazil	29	BA	2916708	Itaquara
Brazil	29	BA	2916807	Itarantim
Brazil	29	BA	2916856	Itatim
Brazil	29	BA	2916906	Itiruçu
Brazil	29	BA	2917003	Itiúba
Brazil	29	BA	2917102	Itororó
Brazil	29	BA	2917201	Ituaçu
Brazil	29	BA	2917300	Ituberá
Brazil	29	BA	2917334	Iuiú
Brazil	29	BA	2917359	Jaborandi
Brazil	29	BA	2917409	Jacaraci
Brazil	29	BA	2917508	Jacobina
Brazil	29	BA	2917607	Jaguaquara
Brazil	29	BA	2917706	Jaguarari
Brazil	29	BA	2917805	Jaguaripe
Brazil	29	BA	2917904	Jandaíra
Brazil	29	BA	2918001	Jequié
Brazil	29	BA	2918100	Jeremoabo
Brazil	29	BA	2918209	Jiquiriçá
Brazil	29	BA	2918308	Jitaúna
Brazil	29	BA	2918357	João Dourado
Brazil	29	BA	2918407	Juazeiro
Brazil	29	BA	2918456	Jucuruçu
Brazil	29	BA	2918506	Jussara
Brazil	29	BA	2918555	Jussari
Brazil	29	BA	2918605	Jussiape
Brazil	29	BA	2918704	Lafaiete Coutinho
Brazil	29	BA	2918753	Lagoa Real
Brazil	29	BA	2918803	Laje
Brazil	29	BA	2918902	Lajedão
Brazil	29	BA	2919009	Lajedinho
Brazil	29	BA	2919058	Lajedo do Tabocal
Brazil	29	BA	2919108	Lamarão
Brazil	29	BA	2919157	Lapão
Brazil	29	BA	2919207	Lauro de Freitas
Brazil	29	BA	2919306	Lençóis
Brazil	29	BA	2919405	Licínio de Almeida
Brazil	29	BA	2919504	Livramento de Nossa Senhora
Brazil	29	BA	2919553	Luís Eduardo Magalhães
Brazil	29	BA	2919603	Macajuba
Brazil	29	BA	2919702	Macarani
Brazil	29	BA	2919801	Macaúbas
Brazil	29	BA	2919900	Macururé
Brazil	29	BA	2919926	Madre de Deus
Brazil	29	BA	2919959	Maetinga
Brazil	29	BA	2920007	Maiquinique
Brazil	29	BA	2920106	Mairi
Brazil	29	BA	2920205	Malhada
Brazil	29	BA	2920304	Malhada de Pedras
Brazil	29	BA	2920403	Manoel Vitorino
Brazil	29	BA	2920452	Mansidão
Brazil	29	BA	2920502	Maracás
Brazil	29	BA	2920601	Maragogipe
Brazil	29	BA	2920700	Maraú
Brazil	29	BA	2920809	Marcionílio Souza
Brazil	29	BA	2920908	Mascote
Brazil	29	BA	2921005	Mata de São João
Brazil	29	BA	2921054	Matina
Brazil	29	BA	2921104	Medeiros Neto
Brazil	29	BA	2921203	Miguel Calmon
Brazil	29	BA	2921302	Milagres
Brazil	29	BA	2921401	Mirangaba
Brazil	29	BA	2921450	Mirante
Brazil	29	BA	2921500	Monte Santo
Brazil	29	BA	2921609	Morpará
Brazil	29	BA	2921708	Morro do Chapéu
Brazil	29	BA	2921807	Mortugaba
Brazil	29	BA	2921906	Mucugê
Brazil	29	BA	2922003	Mucuri
Brazil	29	BA	2922052	Mulungu do Morro
Brazil	29	BA	2922102	Mundo Novo
Brazil	29	BA	2922201	Muniz Ferreira
Brazil	29	BA	2922250	Muquém de São Francisco
Brazil	29	BA	2922300	Muritiba
Brazil	29	BA	2922409	Mutuípe
Brazil	29	BA	2922508	Nazaré
Brazil	29	BA	2922607	Nilo Peçanha
Brazil	29	BA	2922656	Nordestina
Brazil	29	BA	2922706	Nova Canaã
Brazil	29	BA	2922730	Nova Fátima
Brazil	29	BA	2922755	Nova Ibiá
Brazil	29	BA	2922805	Nova Itarana
Brazil	29	BA	2922854	Nova Redenção
Brazil	29	BA	2922904	Nova Soure
Brazil	29	BA	2923001	Nova Viçosa
Brazil	29	BA	2923035	Novo Horizonte
Brazil	29	BA	2923050	Novo Triunfo
Brazil	29	BA	2923100	Olindina
Brazil	29	BA	2923209	Oliveira dos Brejinhos
Brazil	29	BA	2923308	Ouriçangas
Brazil	29	BA	2923357	Ourolândia
Brazil	29	BA	2923407	Palmas de Monte Alto
Brazil	29	BA	2923506	Palmeiras
Brazil	29	BA	2923605	Paramirim
Brazil	29	BA	2923704	Paratinga
Brazil	29	BA	2923803	Paripiranga
Brazil	29	BA	2923902	Pau Brasil
Brazil	29	BA	2924009	Paulo Afonso
Brazil	29	BA	2924058	Pé de Serra
Brazil	29	BA	2924108	Pedrão
Brazil	29	BA	2924207	Pedro Alexandre
Brazil	29	BA	2924306	Piatã
Brazil	29	BA	2924405	Pilão Arcado
Brazil	29	BA	2924504	Pindaí
Brazil	29	BA	2924603	Pindobaçu
Brazil	29	BA	2924652	Pintadas
Brazil	29	BA	2924678	Piraí do Norte
Brazil	29	BA	2924702	Piripá
Brazil	29	BA	2924801	Piritiba
Brazil	29	BA	2924900	Planaltino
Brazil	29	BA	2925006	Planalto
Brazil	29	BA	2925105	Poções
Brazil	29	BA	2925204	Pojuca
Brazil	29	BA	2925253	Ponto Novo
Brazil	29	BA	2925303	Porto Seguro
Brazil	29	BA	2925402	Potiraguá
Brazil	29	BA	2925501	Prado
Brazil	29	BA	2925600	Presidente Dutra
Brazil	29	BA	2925709	Presidente Jânio Quadros
Brazil	29	BA	2925758	Presidente Tancredo Neves
Brazil	29	BA	2925808	Queimadas
Brazil	29	BA	2925907	Quijingue
Brazil	29	BA	2925931	Quixabeira
Brazil	29	BA	2925956	Rafael Jambeiro
Brazil	29	BA	2926004	Remanso
Brazil	29	BA	2926103	Retirolândia
Brazil	29	BA	2926202	Riachão das Neves
Brazil	29	BA	2926301	Riachão do Jacuípe
Brazil	29	BA	2926400	Riacho de Santana
Brazil	29	BA	2926509	Ribeira do Amparo
Brazil	29	BA	2926608	Ribeira do Pombal
Brazil	29	BA	2926657	Ribeirão do Largo
Brazil	29	BA	2926707	Rio de Contas
Brazil	29	BA	2926806	Rio do Antônio
Brazil	29	BA	2926905	Rio do Pires
Brazil	29	BA	2927002	Rio Real
Brazil	29	BA	2927101	Rodelas
Brazil	29	BA	2927200	Ruy Barbosa
Brazil	29	BA	2927309	Salinas da Margarida
Brazil	29	BA	2927408	Salvador
Brazil	29	BA	2927507	Santa Bárbara
Brazil	29	BA	2927606	Santa Brígida
Brazil	29	BA	2927705	Santa Cruz Cabrália
Brazil	29	BA	2927804	Santa Cruz da Vitória
Brazil	29	BA	2927903	Santa Inês
Brazil	29	BA	2928059	Santa Luzia
Brazil	29	BA	2928109	Santa Maria da Vitória
Brazil	29	BA	2928406	Santa Rita de Cássia
Brazil	29	BA	2928505	Santa Teresinha
Brazil	29	BA	2928000	Santaluz
Brazil	29	BA	2928208	Santana
Brazil	29	BA	2928307	Santanópolis
Brazil	29	BA	2928604	Santo Amaro
Brazil	29	BA	2928703	Santo Antônio de Jesus
Brazil	29	BA	2928802	Santo Estêvão
Brazil	29	BA	2928901	São Desidério
Brazil	29	BA	2928950	São Domingos
Brazil	29	BA	2929107	São Felipe
Brazil	29	BA	2929008	São Félix
Brazil	29	BA	2929057	São Félix do Coribe
Brazil	29	BA	2929206	São Francisco do Conde
Brazil	29	BA	2929255	São Gabriel
Brazil	29	BA	2929305	São Gonçalo dos Campos
Brazil	29	BA	2929354	São José da Vitória
Brazil	29	BA	2929370	São José do Jacuípe
Brazil	29	BA	2929404	São Miguel das Matas
Brazil	29	BA	2929503	São Sebastião do Passé
Brazil	29	BA	2929602	Sapeaçu
Brazil	29	BA	2929701	Sátiro Dias
Brazil	29	BA	2929750	Saubara
Brazil	29	BA	2929800	Saúde
Brazil	29	BA	2929909	Seabra
Brazil	29	BA	2930006	Sebastião Laranjeiras
Brazil	29	BA	2930105	Senhor do Bonfim
Brazil	29	BA	2930204	Sento Sé
Brazil	29	BA	2930154	Serra do Ramalho
Brazil	29	BA	2930303	Serra Dourada
Brazil	29	BA	2930402	Serra Preta
Brazil	29	BA	2930501	Serrinha
Brazil	29	BA	2930600	Serrolândia
Brazil	29	BA	2930709	Simões Filho
Brazil	29	BA	2930758	Sítio do Mato
Brazil	29	BA	2930766	Sítio do Quinto
Brazil	29	BA	2930774	Sobradinho
Brazil	29	BA	2930808	Souto Soares
Brazil	29	BA	2930907	Tabocas do Brejo Velho
Brazil	29	BA	2931004	Tanhaçu
Brazil	29	BA	2931053	Tanque Novo
Brazil	29	BA	2931103	Tanquinho
Brazil	29	BA	2931202	Taperoá
Brazil	29	BA	2931301	Tapiramutá
Brazil	29	BA	2931350	Teixeira de Freitas
Brazil	29	BA	2931400	Teodoro Sampaio
Brazil	29	BA	2931509	Teofilândia
Brazil	29	BA	2931608	Teolândia
Brazil	29	BA	2931707	Terra Nova
Brazil	29	BA	2931806	Tremedal
Brazil	29	BA	2931905	Tucano
Brazil	29	BA	2932002	Uauá
Brazil	29	BA	2932101	Ubaíra
Brazil	29	BA	2932200	Ubaitaba
Brazil	29	BA	2932309	Ubatã
Brazil	29	BA	2932408	Uibaí
Brazil	29	BA	2932457	Umburanas
Brazil	29	BA	2932507	Una
Brazil	29	BA	2932606	Urandi
Brazil	29	BA	2932705	Uruçuca
Brazil	29	BA	2932804	Utinga
Brazil	29	BA	2932903	Valença
Brazil	29	BA	2933000	Valente
Brazil	29	BA	2933059	Várzea da Roça
Brazil	29	BA	2933109	Várzea do Poço
Brazil	29	BA	2933158	Várzea Nova
Brazil	29	BA	2933174	Varzedo
Brazil	29	BA	2933208	Vera Cruz
Brazil	29	BA	2933257	Vereda
Brazil	29	BA	2933307	Vitória da Conquista
Brazil	29	BA	2933406	Wagner
Brazil	29	BA	2933455	Wanderley
Brazil	29	BA	2933505	Wenceslau Guimarães
Brazil	29	BA	2933604	Xique-Xique
Brazil	43	RS	4300034	Aceguá
Brazil	43	RS	4300059	Água Santa
Brazil	43	RS	4300109	Agudo
Brazil	43	RS	4300208	Ajuricaba
Brazil	43	RS	4300307	Alecrim
Brazil	43	RS	4300406	Alegrete
Brazil	43	RS	4300455	Alegria
Brazil	43	RS	4300471	Almirante Tamandaré do Sul
Brazil	43	RS	4300505	Alpestre
Brazil	43	RS	4300554	Alto Alegre
Brazil	43	RS	4300570	Alto Feliz
Brazil	43	RS	4300604	Alvorada
Brazil	43	RS	4300638	Amaral Ferrador
Brazil	43	RS	4300646	Ametista do Sul
Brazil	43	RS	4300661	André da Rocha
Brazil	43	RS	4300703	Anta Gorda
Brazil	43	RS	4300802	Antônio Prado
Brazil	43	RS	4300851	Arambaré
Brazil	43	RS	4300877	Araricá
Brazil	43	RS	4300901	Aratiba
Brazil	43	RS	4301008	Arroio do Meio
Brazil	43	RS	4301073	Arroio do Padre
Brazil	43	RS	4301057	Arroio do Sal
Brazil	43	RS	4301206	Arroio do Tigre
Brazil	43	RS	4301107	Arroio dos Ratos
Brazil	43	RS	4301305	Arroio Grande
Brazil	43	RS	4301404	Arvorezinha
Brazil	43	RS	4301503	Augusto Pestana
Brazil	43	RS	4301552	Áurea
Brazil	43	RS	4301602	Bagé
Brazil	43	RS	4301636	Balneário Pinhal
Brazil	43	RS	4301651	Barão
Brazil	43	RS	4301701	Barão de Cotegipe
Brazil	43	RS	4301750	Barão do Triunfo
Brazil	43	RS	4301859	Barra do Guarita
Brazil	43	RS	4301875	Barra do Quaraí
Brazil	43	RS	4301909	Barra do Ribeiro
Brazil	43	RS	4301925	Barra do Rio Azul
Brazil	43	RS	4301958	Barra Funda
Brazil	43	RS	4301800	Barracão
Brazil	43	RS	4302006	Barros Cassal
Brazil	43	RS	4302055	Benjamin Constant do Sul
Brazil	43	RS	4302105	Bento Gonçalves
Brazil	43	RS	4302154	Boa Vista das Missões
Brazil	43	RS	4302204	Boa Vista do Buricá
Brazil	43	RS	4302220	Boa Vista do Cadeado
Brazil	43	RS	4302238	Boa Vista do Incra
Brazil	43	RS	4302253	Boa Vista do Sul
Brazil	43	RS	4302303	Bom Jesus
Brazil	43	RS	4302352	Bom Princípio
Brazil	43	RS	4302378	Bom Progresso
Brazil	43	RS	4302402	Bom Retiro do Sul
Brazil	43	RS	4302451	Boqueirão do Leão
Brazil	43	RS	4302501	Bossoroca
Brazil	43	RS	4302584	Bozano
Brazil	43	RS	4302600	Braga
Brazil	43	RS	4302659	Brochier
Brazil	43	RS	4302709	Butiá
Brazil	43	RS	4302808	Caçapava do Sul
Brazil	43	RS	4302907	Cacequi
Brazil	43	RS	4303004	Cachoeira do Sul
Brazil	43	RS	4303103	Cachoeirinha
Brazil	43	RS	4303202	Cacique Doble
Brazil	43	RS	4303301	Caibaté
Brazil	43	RS	4303400	Caiçara
Brazil	43	RS	4303509	Camaquã
Brazil	43	RS	4303558	Camargo
Brazil	43	RS	4303608	Cambará do Sul
Brazil	43	RS	4303673	Campestre da Serra
Brazil	43	RS	4303707	Campina das Missões
Brazil	43	RS	4303806	Campinas do Sul
Brazil	43	RS	4303905	Campo Bom
Brazil	43	RS	4304002	Campo Novo
Brazil	43	RS	4304101	Campos Borges
Brazil	43	RS	4304200	Candelária
Brazil	43	RS	4304309	Cândido Godói
Brazil	43	RS	4304358	Candiota
Brazil	43	RS	4304408	Canela
Brazil	43	RS	4304507	Canguçu
Brazil	43	RS	4304606	Canoas
Brazil	43	RS	4304614	Canudos do Vale
Brazil	43	RS	4304622	Capão Bonito do Sul
Brazil	43	RS	4304630	Capão da Canoa
Brazil	43	RS	4304655	Capão do Cipó
Brazil	43	RS	4304663	Capão do Leão
Brazil	43	RS	4304689	Capela de Santana
Brazil	43	RS	4304697	Capitão
Brazil	43	RS	4304671	Capivari do Sul
Brazil	43	RS	4304713	Caraá
Brazil	43	RS	4304705	Carazinho
Brazil	43	RS	4304804	Carlos Barbosa
Brazil	43	RS	4304853	Carlos Gomes
Brazil	43	RS	4304903	Casca
Brazil	43	RS	4304952	Caseiros
Brazil	43	RS	4305009	Catuípe
Brazil	43	RS	4305108	Caxias do Sul
Brazil	43	RS	4305116	Centenário
Brazil	43	RS	4305124	Cerrito
Brazil	43	RS	4305132	Cerro Branco
Brazil	43	RS	4305157	Cerro Grande
Brazil	43	RS	4305173	Cerro Grande do Sul
Brazil	43	RS	4305207	Cerro Largo
Brazil	43	RS	4305306	Chapada
Brazil	43	RS	4305355	Charqueadas
Brazil	43	RS	4305371	Charrua
Brazil	43	RS	4305405	Chiapetta
Brazil	43	RS	4305439	Chuí
Brazil	43	RS	4305447	Chuvisca
Brazil	43	RS	4305454	Cidreira
Brazil	43	RS	4305504	Ciríaco
Brazil	43	RS	4305587	Colinas
Brazil	43	RS	4305603	Colorado
Brazil	43	RS	4305702	Condor
Brazil	43	RS	4305801	Constantina
Brazil	43	RS	4305835	Coqueiro Baixo
Brazil	43	RS	4305850	Coqueiros do Sul
Brazil	43	RS	4305871	Coronel Barros
Brazil	43	RS	4305900	Coronel Bicaco
Brazil	43	RS	4305934	Coronel Pilar
Brazil	43	RS	4305959	Cotiporã
Brazil	43	RS	4305975	Coxilha
Brazil	43	RS	4306007	Crissiumal
Brazil	43	RS	4306056	Cristal
Brazil	43	RS	4306072	Cristal do Sul
Brazil	43	RS	4306106	Cruz Alta
Brazil	43	RS	4306130	Cruzaltense
Brazil	43	RS	4306205	Cruzeiro do Sul
Brazil	43	RS	4306304	David Canabarro
Brazil	43	RS	4306320	Derrubadas
Brazil	43	RS	4306353	Dezesseis de Novembro
Brazil	43	RS	4306379	Dilermando de Aguiar
Brazil	43	RS	4306403	Dois Irmãos
Brazil	43	RS	4306429	Dois Irmãos das Missões
Brazil	43	RS	4306452	Dois Lajeados
Brazil	43	RS	4306502	Dom Feliciano
Brazil	43	RS	4306601	Dom Pedrito
Brazil	43	RS	4306551	Dom Pedro de Alcântara
Brazil	43	RS	4306700	Dona Francisca
Brazil	43	RS	4306734	Doutor Maurício Cardoso
Brazil	43	RS	4306759	Doutor Ricardo
Brazil	43	RS	4306767	Eldorado do Sul
Brazil	43	RS	4306809	Encantado
Brazil	43	RS	4306908	Encruzilhada do Sul
Brazil	43	RS	4306924	Engenho Velho
Brazil	43	RS	4306957	Entre Rios do Sul
Brazil	43	RS	4306932	Entre-Ijuís
Brazil	43	RS	4306973	Erebango
Brazil	43	RS	4307005	Erechim
Brazil	43	RS	4307054	Ernestina
Brazil	43	RS	4307203	Erval Grande
Brazil	43	RS	4307302	Erval Seco
Brazil	43	RS	4307401	Esmeralda
Brazil	43	RS	4307450	Esperança do Sul
Brazil	43	RS	4307500	Espumoso
Brazil	43	RS	4307559	Estação
Brazil	43	RS	4307609	Estância Velha
Brazil	43	RS	4307708	Esteio
Brazil	43	RS	4307807	Estrela
Brazil	43	RS	4307815	Estrela Velha
Brazil	43	RS	4307831	Eugênio de Castro
Brazil	43	RS	4307864	Fagundes Varela
Brazil	43	RS	4307906	Farroupilha
Brazil	43	RS	4308003	Faxinal do Soturno
Brazil	43	RS	4308052	Faxinalzinho
Brazil	43	RS	4308078	Fazenda Vilanova
Brazil	43	RS	4308102	Feliz
Brazil	43	RS	4308201	Flores da Cunha
Brazil	43	RS	4308250	Floriano Peixoto
Brazil	43	RS	4308300	Fontoura Xavier
Brazil	43	RS	4308409	Formigueiro
Brazil	43	RS	4308433	Forquetinha
Brazil	43	RS	4308458	Fortaleza dos Valos
Brazil	43	RS	4308508	Frederico Westphalen
Brazil	43	RS	4308607	Garibaldi
Brazil	43	RS	4308656	Garruchos
Brazil	43	RS	4308706	Gaurama
Brazil	43	RS	4308805	General Câmara
Brazil	43	RS	4308854	Gentil
Brazil	43	RS	4308904	Getúlio Vargas
Brazil	43	RS	4309001	Giruá
Brazil	43	RS	4309050	Glorinha
Brazil	43	RS	4309100	Gramado
Brazil	43	RS	4309126	Gramado dos Loureiros
Brazil	43	RS	4309159	Gramado Xavier
Brazil	43	RS	4309209	Gravataí
Brazil	43	RS	4309258	Guabiju
Brazil	43	RS	4309308	Guaíba
Brazil	43	RS	4309407	Guaporé
Brazil	43	RS	4309506	Guarani das Missões
Brazil	43	RS	4309555	Harmonia
Brazil	43	RS	4307104	Herval
Brazil	43	RS	4309571	Herveiras
Brazil	43	RS	4309605	Horizontina
Brazil	43	RS	4309654	Hulha Negra
Brazil	43	RS	4309704	Humaitá
Brazil	43	RS	4309753	Ibarama
Brazil	43	RS	4309803	Ibiaçá
Brazil	43	RS	4309902	Ibiraiaras
Brazil	43	RS	4309951	Ibirapuitã
Brazil	43	RS	4310009	Ibirubá
Brazil	43	RS	4310108	Igrejinha
Brazil	43	RS	4310207	Ijuí
Brazil	43	RS	4310306	Ilópolis
Brazil	43	RS	4310330	Imbé
Brazil	43	RS	4310363	Imigrante
Brazil	43	RS	4310405	Independência
Brazil	43	RS	4310413	Inhacorá
Brazil	43	RS	4310439	Ipê
Brazil	43	RS	4310462	Ipiranga do Sul
Brazil	43	RS	4310504	Iraí
Brazil	43	RS	4310538	Itaara
Brazil	43	RS	4310553	Itacurubi
Brazil	43	RS	4310579	Itapuca
Brazil	43	RS	4310603	Itaqui
Brazil	43	RS	4310652	Itati
Brazil	43	RS	4310702	Itatiba do Sul
Brazil	43	RS	4310751	Ivorá
Brazil	43	RS	4310801	Ivoti
Brazil	43	RS	4310850	Jaboticaba
Brazil	43	RS	4310876	Jacuizinho
Brazil	43	RS	4310900	Jacutinga
Brazil	43	RS	4311007	Jaguarão
Brazil	43	RS	4311106	Jaguari
Brazil	43	RS	4311122	Jaquirana
Brazil	43	RS	4311130	Jari
Brazil	43	RS	4311155	Jóia
Brazil	43	RS	4311205	Júlio de Castilhos
Brazil	43	RS	4311239	Lagoa Bonita do Sul
Brazil	43	RS	4311270	Lagoa dos Três Cantos
Brazil	43	RS	4311304	Lagoa Vermelha
Brazil	43	RS	4311254	Lagoão
Brazil	43	RS	4311403	Lajeado
Brazil	43	RS	4311429	Lajeado do Bugre
Brazil	43	RS	4311502	Lavras do Sul
Brazil	43	RS	4311601	Liberato Salzano
Brazil	43	RS	4311627	Lindolfo Collor
Brazil	43	RS	4311643	Linha Nova
Brazil	43	RS	4311718	Maçambara
Brazil	43	RS	4311700	Machadinho
Brazil	43	RS	4311734	Mampituba
Brazil	43	RS	4311759	Manoel Viana
Brazil	43	RS	4311775	Maquiné
Brazil	43	RS	4311791	Maratá
Brazil	43	RS	4311809	Marau
Brazil	43	RS	4311908	Marcelino Ramos
Brazil	43	RS	4311981	Mariana Pimentel
Brazil	43	RS	4312005	Mariano Moro
Brazil	43	RS	4312054	Marques de Souza
Brazil	43	RS	4312104	Mata
Brazil	43	RS	4312138	Mato Castelhano
Brazil	43	RS	4312153	Mato Leitão
Brazil	43	RS	4312179	Mato Queimado
Brazil	43	RS	4312203	Maximiliano de Almeida
Brazil	43	RS	4312252	Minas do Leão
Brazil	43	RS	4312302	Miraguaí
Brazil	43	RS	4312351	Montauri
Brazil	43	RS	4312377	Monte Alegre dos Campos
Brazil	43	RS	4312385	Monte Belo do Sul
Brazil	43	RS	4312401	Montenegro
Brazil	43	RS	4312427	Mormaço
Brazil	43	RS	4312443	Morrinhos do Sul
Brazil	43	RS	4312450	Morro Redondo
Brazil	43	RS	4312476	Morro Reuter
Brazil	43	RS	4312500	Mostardas
Brazil	43	RS	4312609	Muçum
Brazil	43	RS	4312617	Muitos Capões
Brazil	43	RS	4312625	Muliterno
Brazil	43	RS	4312658	Não-Me-Toque
Brazil	43	RS	4312674	Nicolau Vergueiro
Brazil	43	RS	4312708	Nonoai
Brazil	43	RS	4312757	Nova Alvorada
Brazil	43	RS	4312807	Nova Araçá
Brazil	43	RS	4312906	Nova Bassano
Brazil	43	RS	4312955	Nova Boa Vista
Brazil	43	RS	4313003	Nova Bréscia
Brazil	43	RS	4313011	Nova Candelária
Brazil	43	RS	4313037	Nova Esperança do Sul
Brazil	43	RS	4313060	Nova Hartz
Brazil	43	RS	4313086	Nova Pádua
Brazil	43	RS	4313102	Nova Palma
Brazil	43	RS	4313201	Nova Petrópolis
Brazil	43	RS	4313300	Nova Prata
Brazil	43	RS	4313334	Nova Ramada
Brazil	43	RS	4313359	Nova Roma do Sul
Brazil	43	RS	4313375	Nova Santa Rita
Brazil	43	RS	4313490	Novo Barreiro
Brazil	43	RS	4313391	Novo Cabrais
Brazil	43	RS	4313409	Novo Hamburgo
Brazil	43	RS	4313425	Novo Machado
Brazil	43	RS	4313441	Novo Tiradentes
Brazil	43	RS	4313466	Novo Xingu
Brazil	43	RS	4313508	Osório
Brazil	43	RS	4313607	Paim Filho
Brazil	43	RS	4313656	Palmares do Sul
Brazil	43	RS	4313706	Palmeira das Missões
Brazil	43	RS	4313805	Palmitinho
Brazil	43	RS	4313904	Panambi
Brazil	43	RS	4313953	Pantano Grande
Brazil	43	RS	4314001	Paraí
Brazil	43	RS	4314027	Paraíso do Sul
Brazil	43	RS	4314035	Pareci Novo
Brazil	43	RS	4314050	Parobé
Brazil	43	RS	4314068	Passa Sete
Brazil	43	RS	4314076	Passo do Sobrado
Brazil	43	RS	4314100	Passo Fundo
Brazil	43	RS	4314134	Paulo Bento
Brazil	43	RS	4314159	Paverama
Brazil	43	RS	4314175	Pedras Altas
Brazil	43	RS	4314209	Pedro Osório
Brazil	43	RS	4314308	Pejuçara
Brazil	43	RS	4314407	Pelotas
Brazil	43	RS	4314423	Picada Café
Brazil	43	RS	4314456	Pinhal
Brazil	43	RS	4314464	Pinhal da Serra
Brazil	43	RS	4314472	Pinhal Grande
Brazil	43	RS	4314498	Pinheirinho do Vale
Brazil	43	RS	4314506	Pinheiro Machado
Brazil	43	RS	4314555	Pirapó
Brazil	43	RS	4314605	Piratini
Brazil	43	RS	4314704	Planalto
Brazil	43	RS	4314753	Poço das Antas
Brazil	43	RS	4314779	Pontão
Brazil	43	RS	4314787	Ponte Preta
Brazil	43	RS	4314803	Portão
Brazil	43	RS	4314902	Porto Alegre
Brazil	43	RS	4315008	Porto Lucena
Brazil	43	RS	4315057	Porto Mauá
Brazil	43	RS	4315073	Porto Vera Cruz
Brazil	43	RS	4315107	Porto Xavier
Brazil	43	RS	4315131	Pouso Novo
Brazil	43	RS	4315149	Presidente Lucena
Brazil	43	RS	4315156	Progresso
Brazil	43	RS	4315172	Protásio Alves
Brazil	43	RS	4315206	Putinga
Brazil	43	RS	4315305	Quaraí
Brazil	43	RS	4315313	Quatro Irmãos
Brazil	43	RS	4315321	Quevedos
Brazil	43	RS	4315354	Quinze de Novembro
Brazil	43	RS	4315404	Redentora
Brazil	43	RS	4315453	Relvado
Brazil	43	RS	4315503	Restinga Seca
Brazil	43	RS	4315552	Rio dos Índios
Brazil	43	RS	4315602	Rio Grande
Brazil	43	RS	4315701	Rio Pardo
Brazil	43	RS	4315750	Riozinho
Brazil	43	RS	4315800	Roca Sales
Brazil	43	RS	4315909	Rodeio Bonito
Brazil	43	RS	4315958	Rolador
Brazil	43	RS	4316006	Rolante
Brazil	43	RS	4316105	Ronda Alta
Brazil	43	RS	4316204	Rondinha
Brazil	43	RS	4316303	Roque Gonzales
Brazil	43	RS	4316402	Rosário do Sul
Brazil	43	RS	4316428	Sagrada Família
Brazil	43	RS	4316436	Saldanha Marinho
Brazil	43	RS	4316451	Salto do Jacuí
Brazil	43	RS	4316477	Salvador das Missões
Brazil	43	RS	4316501	Salvador do Sul
Brazil	43	RS	4316600	Sananduva
Brazil	43	RS	4316709	Santa Bárbara do Sul
Brazil	43	RS	4316733	Santa Cecília do Sul
Brazil	43	RS	4316758	Santa Clara do Sul
Brazil	43	RS	4316808	Santa Cruz do Sul
Brazil	43	RS	4316972	Santa Margarida do Sul
Brazil	43	RS	4316907	Santa Maria
Brazil	43	RS	4316956	Santa Maria do Herval
Brazil	43	RS	4317202	Santa Rosa
Brazil	43	RS	4317251	Santa Tereza
Brazil	43	RS	4317301	Santa Vitória do Palmar
Brazil	43	RS	4317004	Santana da Boa Vista
Brazil	43	RS	4317103	Santana do Livramento
Brazil	43	RS	4317400	Santiago
Brazil	43	RS	4317509	Santo Ângelo
Brazil	43	RS	4317608	Santo Antônio da Patrulha
Brazil	43	RS	4317707	Santo Antônio das Missões
Brazil	43	RS	4317558	Santo Antônio do Palma
Brazil	43	RS	4317756	Santo Antônio do Planalto
Brazil	43	RS	4317806	Santo Augusto
Brazil	43	RS	4317905	Santo Cristo
Brazil	43	RS	4317954	Santo Expedito do Sul
Brazil	43	RS	4318002	São Borja
Brazil	43	RS	4318051	São Domingos do Sul
Brazil	43	RS	4318101	São Francisco de Assis
Brazil	43	RS	4318200	São Francisco de Paula
Brazil	43	RS	4318309	São Gabriel
Brazil	43	RS	4318408	São Jerônimo
Brazil	43	RS	4318424	São João da Urtiga
Brazil	43	RS	4318432	São João do Polêsine
Brazil	43	RS	4318440	São Jorge
Brazil	43	RS	4318457	São José das Missões
Brazil	43	RS	4318465	São José do Herval
Brazil	43	RS	4318481	São José do Hortêncio
Brazil	43	RS	4318499	São José do Inhacorá
Brazil	43	RS	4318507	São José do Norte
Brazil	43	RS	4318606	São José do Ouro
Brazil	43	RS	4318614	São José do Sul
Brazil	43	RS	4318622	São José dos Ausentes
Brazil	43	RS	4318705	São Leopoldo
Brazil	43	RS	4318804	São Lourenço do Sul
Brazil	43	RS	4318903	São Luiz Gonzaga
Brazil	43	RS	4319000	São Marcos
Brazil	43	RS	4319109	São Martinho
Brazil	43	RS	4319125	São Martinho da Serra
Brazil	43	RS	4319158	São Miguel das Missões
Brazil	43	RS	4319208	São Nicolau
Brazil	43	RS	4319307	São Paulo das Missões
Brazil	43	RS	4319356	São Pedro da Serra
Brazil	43	RS	4319364	São Pedro das Missões
Brazil	43	RS	4319372	São Pedro do Butiá
Brazil	43	RS	4319406	São Pedro do Sul
Brazil	43	RS	4319505	São Sebastião do Caí
Brazil	43	RS	4319604	São Sepé
Brazil	43	RS	4319703	São Valentim
Brazil	43	RS	4319711	São Valentim do Sul
Brazil	43	RS	4319737	São Valério do Sul
Brazil	43	RS	4319752	São Vendelino
Brazil	43	RS	4319802	São Vicente do Sul
Brazil	43	RS	4319901	Sapiranga
Brazil	43	RS	4320008	Sapucaia do Sul
Brazil	43	RS	4320107	Sarandi
Brazil	43	RS	4320206	Seberi
Brazil	43	RS	4320230	Sede Nova
Brazil	43	RS	4320263	Segredo
Brazil	43	RS	4320305	Selbach
Brazil	43	RS	4320321	Senador Salgado Filho
Brazil	43	RS	4320354	Sentinela do Sul
Brazil	43	RS	4320404	Serafina Corrêa
Brazil	43	RS	4320453	Sério
Brazil	43	RS	4320503	Sertão
Brazil	43	RS	4320552	Sertão Santana
Brazil	43	RS	4320578	Sete de Setembro
Brazil	43	RS	4320602	Severiano de Almeida
Brazil	43	RS	4320651	Silveira Martins
Brazil	43	RS	4320677	Sinimbu
Brazil	43	RS	4320701	Sobradinho
Brazil	43	RS	4320800	Soledade
Brazil	43	RS	4320859	Tabaí
Brazil	43	RS	4320909	Tapejara
Brazil	43	RS	4321006	Tapera
Brazil	43	RS	4321105	Tapes
Brazil	43	RS	4321204	Taquara
Brazil	43	RS	4321303	Taquari
Brazil	43	RS	4321329	Taquaruçu do Sul
Brazil	43	RS	4321352	Tavares
Brazil	43	RS	4321402	Tenente Portela
Brazil	43	RS	4321436	Terra de Areia
Brazil	43	RS	4321451	Teutônia
Brazil	43	RS	4321469	Tio Hugo
Brazil	43	RS	4321477	Tiradentes do Sul
Brazil	43	RS	4321493	Toropi
Brazil	43	RS	4321501	Torres
Brazil	43	RS	4321600	Tramandaí
Brazil	43	RS	4321626	Travesseiro
Brazil	43	RS	4321634	Três Arroios
Brazil	43	RS	4321667	Três Cachoeiras
Brazil	43	RS	4321709	Três Coroas
Brazil	43	RS	4321808	Três de Maio
Brazil	43	RS	4321832	Três Forquilhas
Brazil	43	RS	4321857	Três Palmeiras
Brazil	43	RS	4321907	Três Passos
Brazil	43	RS	4321956	Trindade do Sul
Brazil	43	RS	4322004	Triunfo
Brazil	43	RS	4322103	Tucunduva
Brazil	43	RS	4322152	Tunas
Brazil	43	RS	4322186	Tupanci do Sul
Brazil	43	RS	4322202	Tupanciretã
Brazil	43	RS	4322251	Tupandi
Brazil	43	RS	4322301	Tuparendi
Brazil	43	RS	4322327	Turuçu
Brazil	43	RS	4322343	Ubiretama
Brazil	43	RS	4322350	União da Serra
Brazil	43	RS	4322376	Unistalda
Brazil	43	RS	4322400	Uruguaiana
Brazil	43	RS	4322509	Vacaria
Brazil	43	RS	4322533	Vale do Sol
Brazil	43	RS	4322541	Vale Real
Brazil	43	RS	4322525	Vale Verde
Brazil	43	RS	4322558	Vanini
Brazil	43	RS	4322608	Venâncio Aires
Brazil	43	RS	4322707	Vera Cruz
Brazil	43	RS	4322806	Veranópolis
Brazil	43	RS	4322855	Vespasiano Correa
Brazil	43	RS	4322905	Viadutos
Brazil	43	RS	4323002	Viamão
Brazil	43	RS	4323101	Vicente Dutra
Brazil	43	RS	4323200	Victor Graeff
Brazil	43	RS	4323309	Vila Flores
Brazil	43	RS	4323358	Vila Lângaro
Brazil	43	RS	4323408	Vila Maria
Brazil	43	RS	4323457	Vila Nova do Sul
Brazil	43	RS	4323507	Vista Alegre
Brazil	43	RS	4323606	Vista Alegre do Prata
Brazil	43	RS	4323705	Vista Gaúcha
Brazil	43	RS	4323754	Vitória das Missões
Brazil	43	RS	4323770	Westfalia
Brazil	43	RS	4323804	Xangri-lá
Brazil	35	SP	3500105	Adamantina
Brazil	35	SP	3500204	Adolfo
Brazil	35	SP	3500303	Aguaí
Brazil	35	SP	3500402	Águas da Prata
Brazil	35	SP	3500501	Águas de Lindóia
Brazil	35	SP	3500550	Águas de Santa Bárbara
Brazil	35	SP	3500600	Águas de São Pedro
Brazil	35	SP	3500709	Agudos
Brazil	35	SP	3500758	Alambari
Brazil	35	SP	3500808	Alfredo Marcondes
Brazil	35	SP	3500907	Altair
Brazil	35	SP	3501004	Altinópolis
Brazil	35	SP	3501103	Alto Alegre
Brazil	35	SP	3501152	Alumínio
Brazil	35	SP	3501202	Álvares Florence
Brazil	35	SP	3501301	Álvares Machado
Brazil	35	SP	3501400	Álvaro de Carvalho
Brazil	35	SP	3501509	Alvinlândia
Brazil	35	SP	3501608	Americana
Brazil	35	SP	3501707	Américo Brasiliense
Brazil	35	SP	3501806	Américo de Campos
Brazil	35	SP	3501905	Amparo
Brazil	35	SP	3502002	Analândia
Brazil	35	SP	3502101	Andradina
Brazil	35	SP	3502200	Angatuba
Brazil	35	SP	3502309	Anhembi
Brazil	35	SP	3502408	Anhumas
Brazil	35	SP	3502507	Aparecida
Brazil	35	SP	3502606	Aparecida d'Oeste
Brazil	35	SP	3502705	Apiaí
Brazil	35	SP	3502754	Araçariguama
Brazil	35	SP	3502804	Araçatuba
Brazil	35	SP	3502903	Araçoiaba da Serra
Brazil	35	SP	3503000	Aramina
Brazil	35	SP	3503109	Arandu
Brazil	35	SP	3503158	Arapeí
Brazil	35	SP	3503208	Araraquara
Brazil	35	SP	3503307	Araras
Brazil	35	SP	3503356	Arco-Íris
Brazil	35	SP	3503406	Arealva
Brazil	35	SP	3503505	Areias
Brazil	35	SP	3503604	Areiópolis
Brazil	35	SP	3503703	Ariranha
Brazil	35	SP	3503802	Artur Nogueira
Brazil	35	SP	3503901	Arujá
Brazil	35	SP	3503950	Aspásia
Brazil	35	SP	3504008	Assis
Brazil	35	SP	3504107	Atibaia
Brazil	35	SP	3504206	Auriflama
Brazil	35	SP	3504305	Avaí
Brazil	35	SP	3504404	Avanhandava
Brazil	35	SP	3504503	Avaré
Brazil	35	SP	3504602	Bady Bassitt
Brazil	35	SP	3504701	Balbinos
Brazil	35	SP	3504800	Bálsamo
Brazil	35	SP	3504909	Bananal
Brazil	35	SP	3505005	Barão de Antonina
Brazil	35	SP	3505104	Barbosa
Brazil	35	SP	3505203	Bariri
Brazil	35	SP	3505302	Barra Bonita
Brazil	35	SP	3505351	Barra do Chapéu
Brazil	35	SP	3505401	Barra do Turvo
Brazil	35	SP	3505500	Barretos
Brazil	35	SP	3505609	Barrinha
Brazil	35	SP	3505708	Barueri
Brazil	35	SP	3505807	Bastos
Brazil	35	SP	3505906	Batatais
Brazil	35	SP	3506003	Bauru
Brazil	35	SP	3506102	Bebedouro
Brazil	35	SP	3506201	Bento de Abreu
Brazil	35	SP	3506300	Bernardino de Campos
Brazil	35	SP	3506359	Bertioga
Brazil	35	SP	3506409	Bilac
Brazil	35	SP	3506508	Birigui
Brazil	35	SP	3506607	Biritiba-Mirim
Brazil	35	SP	3506706	Boa Esperança do Sul
Brazil	35	SP	3506805	Bocaina
Brazil	35	SP	3506904	Bofete
Brazil	35	SP	3507001	Boituva
Brazil	35	SP	3507100	Bom Jesus dos Perdões
Brazil	35	SP	3507159	Bom Sucesso de Itararé
Brazil	35	SP	3507209	Borá
Brazil	35	SP	3507308	Boracéia
Brazil	35	SP	3507407	Borborema
Brazil	35	SP	3507456	Borebi
Brazil	35	SP	3507506	Botucatu
Brazil	35	SP	3507605	Bragança Paulista
Brazil	35	SP	3507704	Braúna
Brazil	35	SP	3507753	Brejo Alegre
Brazil	35	SP	3507803	Brodowski
Brazil	35	SP	3507902	Brotas
Brazil	35	SP	3508009	Buri
Brazil	35	SP	3508108	Buritama
Brazil	35	SP	3508207	Buritizal
Brazil	35	SP	3508306	Cabrália Paulista
Brazil	35	SP	3508405	Cabreúva
Brazil	35	SP	3508504	Caçapava
Brazil	35	SP	3508603	Cachoeira Paulista
Brazil	35	SP	3508702	Caconde
Brazil	35	SP	3508801	Cafelândia
Brazil	35	SP	3508900	Caiabu
Brazil	35	SP	3509007	Caieiras
Brazil	35	SP	3509106	Caiuá
Brazil	35	SP	3509205	Cajamar
Brazil	35	SP	3509254	Cajati
Brazil	35	SP	3509304	Cajobi
Brazil	35	SP	3509403	Cajuru
Brazil	35	SP	3509452	Campina do Monte Alegre
Brazil	35	SP	3509502	Campinas
Brazil	35	SP	3509601	Campo Limpo Paulista
Brazil	35	SP	3509700	Campos do Jordão
Brazil	35	SP	3509809	Campos Novos Paulista
Brazil	35	SP	3509908	Cananéia
Brazil	35	SP	3509957	Canas
Brazil	35	SP	3510005	Cândido Mota
Brazil	35	SP	3510104	Cândido Rodrigues
Brazil	35	SP	3510153	Canitar
Brazil	35	SP	3510203	Capão Bonito
Brazil	35	SP	3510302	Capela do Alto
Brazil	35	SP	3510401	Capivari
Brazil	35	SP	3510500	Caraguatatuba
Brazil	35	SP	3510609	Carapicuíba
Brazil	35	SP	3510708	Cardoso
Brazil	35	SP	3510807	Casa Branca
Brazil	35	SP	3510906	Cássia dos Coqueiros
Brazil	35	SP	3511003	Castilho
Brazil	35	SP	3511102	Catanduva
Brazil	35	SP	3511201	Catiguá
Brazil	35	SP	3511300	Cedral
Brazil	35	SP	3511409	Cerqueira César
Brazil	35	SP	3511508	Cerquilho
Brazil	35	SP	3511607	Cesário Lange
Brazil	35	SP	3511706	Charqueada
Brazil	35	SP	3557204	Chavantes
Brazil	35	SP	3511904	Clementina
Brazil	35	SP	3512001	Colina
Brazil	35	SP	3512100	Colômbia
Brazil	35	SP	3512209	Conchal
Brazil	35	SP	3512308	Conchas
Brazil	35	SP	3512407	Cordeirópolis
Brazil	35	SP	3512506	Coroados
Brazil	35	SP	3512605	Coronel Macedo
Brazil	35	SP	3512704	Corumbataí
Brazil	35	SP	3512803	Cosmópolis
Brazil	35	SP	3512902	Cosmorama
Brazil	35	SP	3513009	Cotia
Brazil	35	SP	3513108	Cravinhos
Brazil	35	SP	3513207	Cristais Paulista
Brazil	35	SP	3513306	Cruzália
Brazil	35	SP	3513405	Cruzeiro
Brazil	35	SP	3513504	Cubatão
Brazil	35	SP	3513603	Cunha
Brazil	35	SP	3513702	Descalvado
Brazil	35	SP	3513801	Diadema
Brazil	35	SP	3513850	Dirce Reis
Brazil	35	SP	3513900	Divinolândia
Brazil	35	SP	3514007	Dobrada
Brazil	35	SP	3514106	Dois Córregos
Brazil	35	SP	3514205	Dolcinópolis
Brazil	35	SP	3514304	Dourado
Brazil	35	SP	3514403	Dracena
Brazil	35	SP	3514502	Duartina
Brazil	35	SP	3514601	Dumont
Brazil	35	SP	3514700	Echaporã
Brazil	35	SP	3514809	Eldorado
Brazil	35	SP	3514908	Elias Fausto
Brazil	35	SP	3514924	Elisiário
Brazil	35	SP	3514957	Embaúba
Brazil	35	SP	3515004	Embu
Brazil	35	SP	3515103	Embu-Guaçu
Brazil	35	SP	3515129	Emilianópolis
Brazil	35	SP	3515152	Engenheiro Coelho
Brazil	35	SP	3515186	Espírito Santo do Pinhal
Brazil	35	SP	3515194	Espírito Santo do Turvo
Brazil	35	SP	3557303	Estiva Gerbi
Brazil	35	SP	3515301	Estrela do Norte
Brazil	35	SP	3515202	Estrela d'Oeste
Brazil	35	SP	3515350	Euclides da Cunha Paulista
Brazil	35	SP	3515400	Fartura
Brazil	35	SP	3515608	Fernando Prestes
Brazil	35	SP	3515509	Fernandópolis
Brazil	35	SP	3515657	Fernão
Brazil	35	SP	3515707	Ferraz de Vasconcelos
Brazil	35	SP	3515806	Flora Rica
Brazil	35	SP	3515905	Floreal
Brazil	35	SP	3516002	Flórida Paulista
Brazil	35	SP	3516101	Florínia
Brazil	35	SP	3516200	Franca
Brazil	35	SP	3516309	Francisco Morato
Brazil	35	SP	3516408	Franco da Rocha
Brazil	35	SP	3516507	Gabriel Monteiro
Brazil	35	SP	3516606	Gália
Brazil	35	SP	3516705	Garça
Brazil	35	SP	3516804	Gastão Vidigal
Brazil	35	SP	3516853	Gavião Peixoto
Brazil	35	SP	3516903	General Salgado
Brazil	35	SP	3517000	Getulina
Brazil	35	SP	3517109	Glicério
Brazil	35	SP	3517208	Guaiçara
Brazil	35	SP	3517307	Guaimbê
Brazil	35	SP	3517406	Guaíra
Brazil	35	SP	3517505	Guapiaçu
Brazil	35	SP	3517604	Guapiara
Brazil	35	SP	3517703	Guará
Brazil	35	SP	3517802	Guaraçaí
Brazil	35	SP	3517901	Guaraci
Brazil	35	SP	3518008	Guarani d'Oeste
Brazil	35	SP	3518107	Guarantã
Brazil	35	SP	3518206	Guararapes
Brazil	35	SP	3518305	Guararema
Brazil	35	SP	3518404	Guaratinguetá
Brazil	35	SP	3518503	Guareí
Brazil	35	SP	3518602	Guariba
Brazil	35	SP	3518701	Guarujá
Brazil	35	SP	3518800	Guarulhos
Brazil	35	SP	3518859	Guatapará
Brazil	35	SP	3518909	Guzolândia
Brazil	35	SP	3519006	Herculândia
Brazil	35	SP	3519055	Holambra
Brazil	35	SP	3519071	Hortolândia
Brazil	35	SP	3519105	Iacanga
Brazil	35	SP	3519204	Iacri
Brazil	35	SP	3519253	Iaras
Brazil	35	SP	3519303	Ibaté
Brazil	35	SP	3519402	Ibirá
Brazil	35	SP	3519501	Ibirarema
Brazil	35	SP	3519600	Ibitinga
Brazil	35	SP	3519709	Ibiúna
Brazil	35	SP	3519808	Icém
Brazil	35	SP	3519907	Iepê
Brazil	35	SP	3520004	Igaraçu do Tietê
Brazil	35	SP	3520103	Igarapava
Brazil	35	SP	3520202	Igaratá
Brazil	35	SP	3520301	Iguape
Brazil	35	SP	3520426	Ilha Comprida
Brazil	35	SP	3520442	Ilha Solteira
Brazil	35	SP	3520400	Ilhabela
Brazil	35	SP	3520509	Indaiatuba
Brazil	35	SP	3520608	Indiana
Brazil	35	SP	3520707	Indiaporã
Brazil	35	SP	3520806	Inúbia Paulista
Brazil	35	SP	3520905	Ipaussu
Brazil	35	SP	3521002	Iperó
Brazil	35	SP	3521101	Ipeúna
Brazil	35	SP	3521150	Ipiguá
Brazil	35	SP	3521200	Iporanga
Brazil	35	SP	3521309	Ipuã
Brazil	35	SP	3521408	Iracemápolis
Brazil	35	SP	3521507	Irapuã
Brazil	35	SP	3521606	Irapuru
Brazil	35	SP	3521705	Itaberá
Brazil	35	SP	3521804	Itaí
Brazil	35	SP	3521903	Itajobi
Brazil	35	SP	3522000	Itaju
Brazil	35	SP	3522109	Itanhaém
Brazil	35	SP	3522158	Itaóca
Brazil	35	SP	3522208	Itapecerica da Serra
Brazil	35	SP	3522307	Itapetininga
Brazil	35	SP	3522406	Itapeva
Brazil	35	SP	3522505	Itapevi
Brazil	35	SP	3522604	Itapira
Brazil	35	SP	3522653	Itapirapuã Paulista
Brazil	35	SP	3522703	Itápolis
Brazil	35	SP	3522802	Itaporanga
Brazil	35	SP	3522901	Itapuí
Brazil	35	SP	3523008	Itapura
Brazil	35	SP	3523107	Itaquaquecetuba
Brazil	35	SP	3523206	Itararé
Brazil	35	SP	3523305	Itariri
Brazil	35	SP	3523404	Itatiba
Brazil	35	SP	3523503	Itatinga
Brazil	35	SP	3523602	Itirapina
Brazil	35	SP	3523701	Itirapuã
Brazil	35	SP	3523800	Itobi
Brazil	35	SP	3523909	Itu
Brazil	35	SP	3524006	Itupeva
Brazil	35	SP	3524105	Ituverava
Brazil	35	SP	3524204	Jaborandi
Brazil	35	SP	3524303	Jaboticabal
Brazil	35	SP	3524402	Jacareí
Brazil	35	SP	3524501	Jaci
Brazil	35	SP	3524600	Jacupiranga
Brazil	35	SP	3524709	Jaguariúna
Brazil	35	SP	3524808	Jales
Brazil	35	SP	3524907	Jambeiro
Brazil	35	SP	3525003	Jandira
Brazil	35	SP	3525102	Jardinópolis
Brazil	35	SP	3525201	Jarinu
Brazil	35	SP	3525300	Jaú
Brazil	35	SP	3525409	Jeriquara
Brazil	35	SP	3525508	Joanópolis
Brazil	35	SP	3525607	João Ramalho
Brazil	35	SP	3525706	José Bonifácio
Brazil	35	SP	3525805	Júlio Mesquita
Brazil	35	SP	3525854	Jumirim
Brazil	35	SP	3525904	Jundiaí
Brazil	35	SP	3526001	Junqueirópolis
Brazil	35	SP	3526100	Juquiá
Brazil	35	SP	3526209	Juquitiba
Brazil	35	SP	3526308	Lagoinha
Brazil	35	SP	3526407	Laranjal Paulista
Brazil	35	SP	3526506	Lavínia
Brazil	35	SP	3526605	Lavrinhas
Brazil	35	SP	3526704	Leme
Brazil	35	SP	3526803	Lençóis Paulista
Brazil	35	SP	3526902	Limeira
Brazil	35	SP	3527009	Lindóia
Brazil	35	SP	3527108	Lins
Brazil	35	SP	3527207	Lorena
Brazil	35	SP	3527256	Lourdes
Brazil	35	SP	3527306	Louveira
Brazil	35	SP	3527405	Lucélia
Brazil	35	SP	3527504	Lucianópolis
Brazil	35	SP	3527603	Luís Antônio
Brazil	35	SP	3527702	Luiziânia
Brazil	35	SP	3527801	Lupércio
Brazil	35	SP	3527900	Lutécia
Brazil	35	SP	3528007	Macatuba
Brazil	35	SP	3528106	Macaubal
Brazil	35	SP	3528205	Macedônia
Brazil	35	SP	3528304	Magda
Brazil	35	SP	3528403	Mairinque
Brazil	35	SP	3528502	Mairiporã
Brazil	35	SP	3528601	Manduri
Brazil	35	SP	3528700	Marabá Paulista
Brazil	35	SP	3528809	Maracaí
Brazil	35	SP	3528858	Marapoama
Brazil	35	SP	3528908	Mariápolis
Brazil	35	SP	3529005	Marília
Brazil	35	SP	3529104	Marinópolis
Brazil	35	SP	3529203	Martinópolis
Brazil	35	SP	3529302	Matão
Brazil	35	SP	3529401	Mauá
Brazil	35	SP	3529500	Mendonça
Brazil	35	SP	3529609	Meridiano
Brazil	35	SP	3529658	Mesópolis
Brazil	35	SP	3529708	Miguelópolis
Brazil	35	SP	3529807	Mineiros do Tietê
Brazil	35	SP	3530003	Mira Estrela
Brazil	35	SP	3529906	Miracatu
Brazil	35	SP	3530102	Mirandópolis
Brazil	35	SP	3530201	Mirante do Paranapanema
Brazil	35	SP	3530300	Mirassol
Brazil	35	SP	3530409	Mirassolândia
Brazil	35	SP	3530508	Mococa
Brazil	35	SP	3530607	Mogi das Cruzes
Brazil	35	SP	3530706	Mogi Guaçu
Brazil	35	SP	3530805	Moji Mirim
Brazil	35	SP	3530904	Mombuca
Brazil	35	SP	3531001	Monções
Brazil	35	SP	3531100	Mongaguá
Brazil	35	SP	3531209	Monte Alegre do Sul
Brazil	35	SP	3531308	Monte Alto
Brazil	35	SP	3531407	Monte Aprazível
Brazil	35	SP	3531506	Monte Azul Paulista
Brazil	35	SP	3531605	Monte Castelo
Brazil	35	SP	3531803	Monte Mor
Brazil	35	SP	3531704	Monteiro Lobato
Brazil	35	SP	3531902	Morro Agudo
Brazil	35	SP	3532009	Morungaba
Brazil	35	SP	3532058	Motuca
Brazil	35	SP	3532108	Murutinga do Sul
Brazil	35	SP	3532157	Nantes
Brazil	35	SP	3532207	Narandiba
Brazil	35	SP	3532306	Natividade da Serra
Brazil	35	SP	3532405	Nazaré Paulista
Brazil	35	SP	3532504	Neves Paulista
Brazil	35	SP	3532603	Nhandeara
Brazil	35	SP	3532702	Nipoã
Brazil	35	SP	3532801	Nova Aliança
Brazil	35	SP	3532827	Nova Campina
Brazil	35	SP	3532843	Nova Canaã Paulista
Brazil	35	SP	3532868	Nova Castilho
Brazil	35	SP	3532900	Nova Europa
Brazil	35	SP	3533007	Nova Granada
Brazil	35	SP	3533106	Nova Guataporanga
Brazil	35	SP	3533205	Nova Independência
Brazil	35	SP	3533304	Nova Luzitânia
Brazil	35	SP	3533403	Nova Odessa
Brazil	35	SP	3533254	Novais
Brazil	35	SP	3533502	Novo Horizonte
Brazil	35	SP	3533601	Nuporanga
Brazil	35	SP	3533700	Ocauçu
Brazil	35	SP	3533809	Óleo
Brazil	35	SP	3533908	Olímpia
Brazil	35	SP	3534005	Onda Verde
Brazil	35	SP	3534104	Oriente
Brazil	35	SP	3534203	Orindiúva
Brazil	35	SP	3534302	Orlândia
Brazil	35	SP	3534401	Osasco
Brazil	35	SP	3534500	Oscar Bressane
Brazil	35	SP	3534609	Osvaldo Cruz
Brazil	35	SP	3534708	Ourinhos
Brazil	35	SP	3534807	Ouro Verde
Brazil	35	SP	3534757	Ouroeste
Brazil	35	SP	3534906	Pacaembu
Brazil	35	SP	3535002	Palestina
Brazil	35	SP	3535101	Palmares Paulista
Brazil	35	SP	3535200	Palmeira d'Oeste
Brazil	35	SP	3535309	Palmital
Brazil	35	SP	3535408	Panorama
Brazil	35	SP	3535507	Paraguaçu Paulista
Brazil	35	SP	3535606	Paraibuna
Brazil	35	SP	3535705	Paraíso
Brazil	35	SP	3535804	Paranapanema
Brazil	35	SP	3535903	Paranapuã
Brazil	35	SP	3536000	Parapuã
Brazil	35	SP	3536109	Pardinho
Brazil	35	SP	3536208	Pariquera-Açu
Brazil	35	SP	3536257	Parisi
Brazil	35	SP	3536307	Patrocínio Paulista
Brazil	35	SP	3536406	Paulicéia
Brazil	35	SP	3536505	Paulínia
Brazil	35	SP	3536570	Paulistânia
Brazil	35	SP	3536604	Paulo de Faria
Brazil	35	SP	3536703	Pederneiras
Brazil	35	SP	3536802	Pedra Bela
Brazil	35	SP	3536901	Pedranópolis
Brazil	35	SP	3537008	Pedregulho
Brazil	35	SP	3537107	Pedreira
Brazil	35	SP	3537156	Pedrinhas Paulista
Brazil	35	SP	3537206	Pedro de Toledo
Brazil	35	SP	3537305	Penápolis
Brazil	35	SP	3537404	Pereira Barreto
Brazil	35	SP	3537503	Pereiras
Brazil	35	SP	3537602	Peruíbe
Brazil	35	SP	3537701	Piacatu
Brazil	35	SP	3537800	Piedade
Brazil	35	SP	3537909	Pilar do Sul
Brazil	35	SP	3538006	Pindamonhangaba
Brazil	35	SP	3538105	Pindorama
Brazil	35	SP	3538204	Pinhalzinho
Brazil	35	SP	3538303	Piquerobi
Brazil	35	SP	3538501	Piquete
Brazil	35	SP	3538600	Piracaia
Brazil	35	SP	3538709	Piracicaba
Brazil	35	SP	3538808	Piraju
Brazil	35	SP	3538907	Pirajuí
Brazil	35	SP	3539004	Pirangi
Brazil	35	SP	3539103	Pirapora do Bom Jesus
Brazil	35	SP	3539202	Pirapozinho
Brazil	35	SP	3539301	Pirassununga
Brazil	35	SP	3539400	Piratininga
Brazil	35	SP	3539509	Pitangueiras
Brazil	35	SP	3539608	Planalto
Brazil	35	SP	3539707	Platina
Brazil	35	SP	3539806	Poá
Brazil	35	SP	3539905	Poloni
Brazil	35	SP	3540002	Pompéia
Brazil	35	SP	3540101	Pongaí
Brazil	35	SP	3540200	Pontal
Brazil	35	SP	3540259	Pontalinda
Brazil	35	SP	3540309	Pontes Gestal
Brazil	35	SP	3540408	Populina
Brazil	35	SP	3540507	Porangaba
Brazil	35	SP	3540606	Porto Feliz
Brazil	35	SP	3540705	Porto Ferreira
Brazil	35	SP	3540754	Potim
Brazil	35	SP	3540804	Potirendaba
Brazil	35	SP	3540853	Pracinha
Brazil	35	SP	3540903	Pradópolis
Brazil	35	SP	3541000	Praia Grande
Brazil	35	SP	3541059	Pratânia
Brazil	35	SP	3541109	Presidente Alves
Brazil	35	SP	3541208	Presidente Bernardes
Brazil	35	SP	3541307	Presidente Epitácio
Brazil	35	SP	3541406	Presidente Prudente
Brazil	35	SP	3541505	Presidente Venceslau
Brazil	35	SP	3541604	Promissão
Brazil	35	SP	3541653	Quadra
Brazil	35	SP	3541703	Quatá
Brazil	35	SP	3541802	Queiroz
Brazil	35	SP	3541901	Queluz
Brazil	35	SP	3542008	Quintana
Brazil	35	SP	3542107	Rafard
Brazil	35	SP	3542206	Rancharia
Brazil	35	SP	3542305	Redenção da Serra
Brazil	35	SP	3542404	Regente Feijó
Brazil	35	SP	3542503	Reginópolis
Brazil	35	SP	3542602	Registro
Brazil	35	SP	3542701	Restinga
Brazil	35	SP	3542800	Ribeira
Brazil	35	SP	3542909	Ribeirão Bonito
Brazil	35	SP	3543006	Ribeirão Branco
Brazil	35	SP	3543105	Ribeirão Corrente
Brazil	35	SP	3543204	Ribeirão do Sul
Brazil	35	SP	3543238	Ribeirão dos Índios
Brazil	35	SP	3543253	Ribeirão Grande
Brazil	35	SP	3543303	Ribeirão Pires
Brazil	35	SP	3543402	Ribeirão Preto
Brazil	35	SP	3543600	Rifaina
Brazil	35	SP	3543709	Rincão
Brazil	35	SP	3543808	Rinópolis
Brazil	35	SP	3543907	Rio Claro
Brazil	35	SP	3544004	Rio das Pedras
Brazil	35	SP	3544103	Rio Grande da Serra
Brazil	35	SP	3544202	Riolândia
Brazil	35	SP	3543501	Riversul
Brazil	35	SP	3544251	Rosana
Brazil	35	SP	3544301	Roseira
Brazil	35	SP	3544400	Rubiácea
Brazil	35	SP	3544509	Rubinéia
Brazil	35	SP	3544608	Sabino
Brazil	35	SP	3544707	Sagres
Brazil	35	SP	3544806	Sales
Brazil	35	SP	3544905	Sales Oliveira
Brazil	35	SP	3545001	Salesópolis
Brazil	35	SP	3545100	Salmourão
Brazil	35	SP	3545159	Saltinho
Brazil	35	SP	3545209	Salto
Brazil	35	SP	3545308	Salto de Pirapora
Brazil	35	SP	3545407	Salto Grande
Brazil	35	SP	3545506	Sandovalina
Brazil	35	SP	3545605	Santa Adélia
Brazil	35	SP	3545704	Santa Albertina
Brazil	35	SP	3545803	Santa Bárbara d'Oeste
Brazil	35	SP	3546009	Santa Branca
Brazil	35	SP	3546108	Santa Clara d'Oeste
Brazil	35	SP	3546207	Santa Cruz da Conceição
Brazil	35	SP	3546256	Santa Cruz da Esperança
Brazil	35	SP	3546306	Santa Cruz das Palmeiras
Brazil	35	SP	3546405	Santa Cruz do Rio Pardo
Brazil	35	SP	3546504	Santa Ernestina
Brazil	35	SP	3546603	Santa Fé do Sul
Brazil	35	SP	3546702	Santa Gertrudes
Brazil	35	SP	3546801	Santa Isabel
Brazil	35	SP	3546900	Santa Lúcia
Brazil	35	SP	3547007	Santa Maria da Serra
Brazil	35	SP	3547106	Santa Mercedes
Brazil	35	SP	3547502	Santa Rita do Passa Quatro
Brazil	35	SP	3547403	Santa Rita d'Oeste
Brazil	35	SP	3547601	Santa Rosa de Viterbo
Brazil	35	SP	3547650	Santa Salete
Brazil	35	SP	3547205	Santana da Ponte Pensa
Brazil	35	SP	3547304	Santana de Parnaíba
Brazil	35	SP	3547700	Santo Anastácio
Brazil	35	SP	3547809	Santo André
Brazil	35	SP	3547908	Santo Antônio da Alegria
Brazil	35	SP	3548005	Santo Antônio de Posse
Brazil	35	SP	3548054	Santo Antônio do Aracanguá
Brazil	35	SP	3548104	Santo Antônio do Jardim
Brazil	35	SP	3548203	Santo Antônio do Pinhal
Brazil	35	SP	3548302	Santo Expedito
Brazil	35	SP	3548401	Santópolis do Aguapeí
Brazil	35	SP	3548500	Santos
Brazil	35	SP	3548609	São Bento do Sapucaí
Brazil	35	SP	3548708	São Bernardo do Campo
Brazil	35	SP	3548807	São Caetano do Sul
Brazil	35	SP	3548906	São Carlos
Brazil	35	SP	3549003	São Francisco
Brazil	35	SP	3549102	São João da Boa Vista
Brazil	35	SP	3549201	São João das Duas Pontes
Brazil	35	SP	3549250	São João de Iracema
Brazil	35	SP	3549300	São João do Pau d'Alho
Brazil	35	SP	3549409	São Joaquim da Barra
Brazil	35	SP	3549508	São José da Bela Vista
Brazil	35	SP	3549607	São José do Barreiro
Brazil	35	SP	3549706	São José do Rio Pardo
Brazil	35	SP	3549805	São José do Rio Preto
Brazil	35	SP	3549904	São José dos Campos
Brazil	35	SP	3549953	São Lourenço da Serra
Brazil	35	SP	3550001	São Luís do Paraitinga
Brazil	35	SP	3550100	São Manuel
Brazil	35	SP	3550209	São Miguel Arcanjo
Brazil	35	SP	3550308	São Paulo
Brazil	35	SP	3550407	São Pedro
Brazil	35	SP	3550506	São Pedro do Turvo
Brazil	35	SP	3550605	São Roque
Brazil	35	SP	3550704	São Sebastião
Brazil	35	SP	3550803	São Sebastião da Grama
Brazil	35	SP	3550902	São Simão
Brazil	35	SP	3551009	São Vicente
Brazil	35	SP	3551108	Sarapuí
Brazil	35	SP	3551207	Sarutaiá
Brazil	35	SP	3551306	Sebastianópolis do Sul
Brazil	35	SP	3551405	Serra Azul
Brazil	35	SP	3551603	Serra Negra
Brazil	35	SP	3551504	Serrana
Brazil	35	SP	3551702	Sertãozinho
Brazil	35	SP	3551801	Sete Barras
Brazil	35	SP	3551900	Severínia
Brazil	35	SP	3552007	Silveiras
Brazil	35	SP	3552106	Socorro
Brazil	35	SP	3552205	Sorocaba
Brazil	35	SP	3552304	Sud Mennucci
Brazil	35	SP	3552403	Sumaré
Brazil	35	SP	3552551	Suzanápolis
Brazil	35	SP	3552502	Suzano
Brazil	35	SP	3552601	Tabapuã
Brazil	35	SP	3552700	Tabatinga
Brazil	35	SP	3552809	Taboão da Serra
Brazil	35	SP	3552908	Taciba
Brazil	35	SP	3553005	Taguaí
Brazil	35	SP	3553104	Taiaçu
Brazil	35	SP	3553203	Taiúva
Brazil	35	SP	3553302	Tambaú
Brazil	35	SP	3553401	Tanabi
Brazil	35	SP	3553500	Tapiraí
Brazil	35	SP	3553609	Tapiratiba
Brazil	35	SP	3553658	Taquaral
Brazil	35	SP	3553708	Taquaritinga
Brazil	35	SP	3553807	Taquarituba
Brazil	35	SP	3553856	Taquarivaí
Brazil	35	SP	3553906	Tarabai
Brazil	35	SP	3553955	Tarumã
Brazil	35	SP	3554003	Tatuí
Brazil	35	SP	3554102	Taubaté
Brazil	35	SP	3554201	Tejupá
Brazil	35	SP	3554300	Teodoro Sampaio
Brazil	35	SP	3554409	Terra Roxa
Brazil	35	SP	3554508	Tietê
Brazil	35	SP	3554607	Timburi
Brazil	35	SP	3554656	Torre de Pedra
Brazil	35	SP	3554706	Torrinha
Brazil	35	SP	3554755	Trabiju
Brazil	35	SP	3554805	Tremembé
Brazil	35	SP	3554904	Três Fronteiras
Brazil	35	SP	3554953	Tuiuti
Brazil	35	SP	3555000	Tupã
Brazil	35	SP	3555109	Tupi Paulista
Brazil	35	SP	3555208	Turiúba
Brazil	35	SP	3555307	Turmalina
Brazil	35	SP	3555356	Ubarana
Brazil	35	SP	3555406	Ubatuba
Brazil	35	SP	3555505	Ubirajara
Brazil	35	SP	3555604	Uchoa
Brazil	35	SP	3555703	União Paulista
Brazil	35	SP	3555802	Urânia
Brazil	35	SP	3555901	Uru
Brazil	35	SP	3556008	Urupês
Brazil	35	SP	3556107	Valentim Gentil
Brazil	35	SP	3556206	Valinhos
Brazil	35	SP	3556305	Valparaíso
Brazil	35	SP	3556354	Vargem
Brazil	35	SP	3556404	Vargem Grande do Sul
Brazil	35	SP	3556453	Vargem Grande Paulista
Brazil	35	SP	3556503	Várzea Paulista
Brazil	35	SP	3556602	Vera Cruz
Brazil	35	SP	3556701	Vinhedo
Brazil	35	SP	3556800	Viradouro
Brazil	35	SP	3556909	Vista Alegre do Alto
Brazil	35	SP	3556958	Vitória Brasil
Brazil	35	SP	3557006	Votorantim
Brazil	35	SP	3557105	Votuporanga
Brazil	35	SP	3557154	Zacarias
Brazil	31	MG	3100104	Abadia dos Dourados
Brazil	31	MG	3100203	Abaeté
Brazil	31	MG	3100302	Abre Campo
Brazil	31	MG	3100401	Acaiaca
Brazil	31	MG	3100500	Açucena
Brazil	31	MG	3100609	Água Boa
Brazil	31	MG	3100708	Água Comprida
Brazil	31	MG	3100807	Aguanil
Brazil	31	MG	3100906	Águas Formosas
Brazil	31	MG	3101003	Águas Vermelhas
Brazil	31	MG	3101102	Aimorés
Brazil	31	MG	3101201	Aiuruoca
Brazil	31	MG	3101300	Alagoa
Brazil	31	MG	3101409	Albertina
Brazil	31	MG	3101508	Além Paraíba
Brazil	31	MG	3101607	Alfenas
Brazil	31	MG	3101631	Alfredo Vasconcelos
Brazil	31	MG	3101706	Almenara
Brazil	31	MG	3101805	Alpercata
Brazil	31	MG	3101904	Alpinópolis
Brazil	31	MG	3102001	Alterosa
Brazil	31	MG	3102050	Alto Caparaó
Brazil	31	MG	3153509	Alto Jequitibá
Brazil	31	MG	3102100	Alto Rio Doce
Brazil	31	MG	3102209	Alvarenga
Brazil	31	MG	3102308	Alvinópolis
Brazil	31	MG	3102407	Alvorada de Minas
Brazil	31	MG	3102506	Amparo do Serra
Brazil	31	MG	3102605	Andradas
Brazil	31	MG	3102803	Andrelândia
Brazil	31	MG	3102852	Angelândia
Brazil	31	MG	3102902	Antônio Carlos
Brazil	31	MG	3103009	Antônio Dias
Brazil	31	MG	3103108	Antônio Prado de Minas
Brazil	31	MG	3103207	Araçaí
Brazil	31	MG	3103306	Aracitaba
Brazil	31	MG	3103405	Araçuaí
Brazil	31	MG	3103504	Araguari
Brazil	31	MG	3103603	Arantina
Brazil	31	MG	3103702	Araponga
Brazil	31	MG	3103751	Araporã
Brazil	31	MG	3103801	Arapuá
Brazil	31	MG	3103900	Araújos
Brazil	31	MG	3104007	Araxá
Brazil	31	MG	3104106	Arceburgo
Brazil	31	MG	3104205	Arcos
Brazil	31	MG	3104304	Areado
Brazil	31	MG	3104403	Argirita
Brazil	31	MG	3104452	Aricanduva
Brazil	31	MG	3104502	Arinos
Brazil	31	MG	3104601	Astolfo Dutra
Brazil	31	MG	3104700	Ataléia
Brazil	31	MG	3104809	Augusto de Lima
Brazil	31	MG	3104908	Baependi
Brazil	31	MG	3105004	Baldim
Brazil	31	MG	3105103	Bambuí
Brazil	31	MG	3105202	Bandeira
Brazil	31	MG	3105301	Bandeira do Sul
Brazil	31	MG	3105400	Barão de Cocais
Brazil	31	MG	3105509	Barão de Monte Alto
Brazil	31	MG	3105608	Barbacena
Brazil	31	MG	3105707	Barra Longa
Brazil	31	MG	3105905	Barroso
Brazil	31	MG	3106002	Bela Vista de Minas
Brazil	31	MG	3106101	Belmiro Braga
Brazil	31	MG	3106200	Belo Horizonte
Brazil	31	MG	3106309	Belo Oriente
Brazil	31	MG	3106408	Belo Vale
Brazil	31	MG	3106507	Berilo
Brazil	31	MG	3106655	Berizal
Brazil	31	MG	3106606	Bertópolis
Brazil	31	MG	3106705	Betim
Brazil	31	MG	3106804	Bias Fortes
Brazil	31	MG	3106903	Bicas
Brazil	31	MG	3107000	Biquinhas
Brazil	31	MG	3107109	Boa Esperança
Brazil	31	MG	3107208	Bocaina de Minas
Brazil	31	MG	3107307	Bocaiúva
Brazil	31	MG	3107406	Bom Despacho
Brazil	31	MG	3107505	Bom Jardim de Minas
Brazil	31	MG	3107604	Bom Jesus da Penha
Brazil	31	MG	3107703	Bom Jesus do Amparo
Brazil	31	MG	3107802	Bom Jesus do Galho
Brazil	31	MG	3107901	Bom Repouso
Brazil	31	MG	3108008	Bom Sucesso
Brazil	31	MG	3108107	Bonfim
Brazil	31	MG	3108206	Bonfinópolis de Minas
Brazil	31	MG	3108255	Bonito de Minas
Brazil	31	MG	3108305	Borda da Mata
Brazil	31	MG	3108404	Botelhos
Brazil	31	MG	3108503	Botumirim
Brazil	31	MG	3108701	Brás Pires
Brazil	31	MG	3108552	Brasilândia de Minas
Brazil	31	MG	3108602	Brasília de Minas
Brazil	31	MG	3108909	Brasópolis
Brazil	31	MG	3108800	Braúnas
Brazil	31	MG	3109006	Brumadinho
Brazil	31	MG	3109105	Bueno Brandão
Brazil	31	MG	3109204	Buenópolis
Brazil	31	MG	3109253	Bugre
Brazil	31	MG	3109303	Buritis
Brazil	31	MG	3109402	Buritizeiro
Brazil	31	MG	3109451	Cabeceira Grande
Brazil	31	MG	3109501	Cabo Verde
Brazil	31	MG	3109600	Cachoeira da Prata
Brazil	31	MG	3109709	Cachoeira de Minas
Brazil	31	MG	3102704	Cachoeira de Pajeú
Brazil	31	MG	3109808	Cachoeira Dourada
Brazil	31	MG	3109907	Caetanópolis
Brazil	31	MG	3110004	Caeté
Brazil	31	MG	3110103	Caiana
Brazil	31	MG	3110202	Cajuri
Brazil	31	MG	3110301	Caldas
Brazil	31	MG	3110400	Camacho
Brazil	31	MG	3110509	Camanducaia
Brazil	31	MG	3110608	Cambuí
Brazil	31	MG	3110707	Cambuquira
Brazil	31	MG	3110806	Campanário
Brazil	31	MG	3110905	Campanha
Brazil	31	MG	3111002	Campestre
Brazil	31	MG	3111101	Campina Verde
Brazil	31	MG	3111150	Campo Azul
Brazil	31	MG	3111200	Campo Belo
Brazil	31	MG	3111309	Campo do Meio
Brazil	31	MG	3111408	Campo Florido
Brazil	31	MG	3111507	Campos Altos
Brazil	31	MG	3111606	Campos Gerais
Brazil	31	MG	3111903	Cana Verde
Brazil	31	MG	3111705	Canaã
Brazil	31	MG	3111804	Canápolis
Brazil	31	MG	3112000	Candeias
Brazil	31	MG	3112059	Cantagalo
Brazil	31	MG	3112109	Caparaó
Brazil	31	MG	3112208	Capela Nova
Brazil	31	MG	3112307	Capelinha
Brazil	31	MG	3112406	Capetinga
Brazil	31	MG	3112505	Capim Branco
Brazil	31	MG	3112604	Capinópolis
Brazil	31	MG	3112653	Capitão Andrade
Brazil	31	MG	3112703	Capitão Enéas
Brazil	31	MG	3112802	Capitólio
Brazil	31	MG	3112901	Caputira
Brazil	31	MG	3113008	Caraí
Brazil	31	MG	3113107	Caranaíba
Brazil	31	MG	3113206	Carandaí
Brazil	31	MG	3113305	Carangola
Brazil	31	MG	3113404	Caratinga
Brazil	31	MG	3113503	Carbonita
Brazil	31	MG	3113602	Careaçu
Brazil	31	MG	3113701	Carlos Chagas
Brazil	31	MG	3113800	Carmésia
Brazil	31	MG	3113909	Carmo da Cachoeira
Brazil	31	MG	3114006	Carmo da Mata
Brazil	31	MG	3114105	Carmo de Minas
Brazil	31	MG	3114204	Carmo do Cajuru
Brazil	31	MG	3114303	Carmo do Paranaíba
Brazil	31	MG	3114402	Carmo do Rio Claro
Brazil	31	MG	3114501	Carmópolis de Minas
Brazil	31	MG	3114550	Carneirinho
Brazil	31	MG	3114600	Carrancas
Brazil	31	MG	3114709	Carvalhópolis
Brazil	31	MG	3114808	Carvalhos
Brazil	31	MG	3114907	Casa Grande
Brazil	31	MG	3115003	Cascalho Rico
Brazil	31	MG	3115102	Cássia
Brazil	31	MG	3115300	Cataguases
Brazil	31	MG	3115359	Catas Altas
Brazil	31	MG	3115409	Catas Altas da Noruega
Brazil	31	MG	3115458	Catuji
Brazil	31	MG	3115474	Catuti
Brazil	31	MG	3115508	Caxambu
Brazil	31	MG	3115607	Cedro do Abaeté
Brazil	31	MG	3115706	Central de Minas
Brazil	31	MG	3115805	Centralina
Brazil	31	MG	3115904	Chácara
Brazil	31	MG	3116001	Chalé
Brazil	31	MG	3116100	Chapada do Norte
Brazil	31	MG	3116159	Chapada Gaúcha
Brazil	31	MG	3116209	Chiador
Brazil	31	MG	3116308	Cipotânea
Brazil	31	MG	3116407	Claraval
Brazil	31	MG	3116506	Claro dos Poções
Brazil	31	MG	3116605	Cláudio
Brazil	31	MG	3116704	Coimbra
Brazil	31	MG	3116803	Coluna
Brazil	31	MG	3116902	Comendador Gomes
Brazil	31	MG	3117009	Comercinho
Brazil	31	MG	3117108	Conceição da Aparecida
Brazil	31	MG	3115201	Conceição da Barra de Minas
Brazil	31	MG	3117306	Conceição das Alagoas
Brazil	31	MG	3117207	Conceição das Pedras
Brazil	31	MG	3117405	Conceição de Ipanema
Brazil	31	MG	3117504	Conceição do Mato Dentro
Brazil	31	MG	3117603	Conceição do Pará
Brazil	31	MG	3117702	Conceição do Rio Verde
Brazil	31	MG	3117801	Conceição dos Ouros
Brazil	31	MG	3117836	Cônego Marinho
Brazil	31	MG	3117876	Confins
Brazil	31	MG	3117900	Congonhal
Brazil	31	MG	3118007	Congonhas
Brazil	31	MG	3118106	Congonhas do Norte
Brazil	31	MG	3118205	Conquista
Brazil	31	MG	3118304	Conselheiro Lafaiete
Brazil	31	MG	3118403	Conselheiro Pena
Brazil	31	MG	3118502	Consolação
Brazil	31	MG	3118601	Contagem
Brazil	31	MG	3118700	Coqueiral
Brazil	31	MG	3118809	Coração de Jesus
Brazil	31	MG	3118908	Cordisburgo
Brazil	31	MG	3119005	Cordislândia
Brazil	31	MG	3119104	Corinto
Brazil	31	MG	3119203	Coroaci
Brazil	31	MG	3119302	Coromandel
Brazil	31	MG	3119401	Coronel Fabriciano
Brazil	31	MG	3119500	Coronel Murta
Brazil	31	MG	3119609	Coronel Pacheco
Brazil	31	MG	3119708	Coronel Xavier Chaves
Brazil	31	MG	3119807	Córrego Danta
Brazil	31	MG	3119906	Córrego do Bom Jesus
Brazil	31	MG	3119955	Córrego Fundo
Brazil	31	MG	3120003	Córrego Novo
Brazil	31	MG	3120102	Couto de Magalhães de Minas
Brazil	31	MG	3120151	Crisólita
Brazil	31	MG	3120201	Cristais
Brazil	31	MG	3120300	Cristália
Brazil	31	MG	3120409	Cristiano Otoni
Brazil	31	MG	3120508	Cristina
Brazil	31	MG	3120607	Crucilândia
Brazil	31	MG	3120706	Cruzeiro da Fortaleza
Brazil	31	MG	3120805	Cruzília
Brazil	31	MG	3120839	Cuparaque
Brazil	31	MG	3120870	Curral de Dentro
Brazil	31	MG	3120904	Curvelo
Brazil	31	MG	3121001	Datas
Brazil	31	MG	3121100	Delfim Moreira
Brazil	31	MG	3121209	Delfinópolis
Brazil	31	MG	3121258	Delta
Brazil	31	MG	3121308	Descoberto
Brazil	31	MG	3121407	Desterro de Entre Rios
Brazil	31	MG	3121506	Desterro do Melo
Brazil	31	MG	3121605	Diamantina
Brazil	31	MG	3121704	Diogo de Vasconcelos
Brazil	31	MG	3121803	Dionísio
Brazil	31	MG	3121902	Divinésia
Brazil	31	MG	3122009	Divino
Brazil	31	MG	3122108	Divino das Laranjeiras
Brazil	31	MG	3122207	Divinolândia de Minas
Brazil	31	MG	3122306	Divinópolis
Brazil	31	MG	3122355	Divisa Alegre
Brazil	31	MG	3122405	Divisa Nova
Brazil	31	MG	3122454	Divisópolis
Brazil	31	MG	3122470	Dom Bosco
Brazil	31	MG	3122504	Dom Cavati
Brazil	31	MG	3122603	Dom Joaquim
Brazil	31	MG	3122702	Dom Silvério
Brazil	31	MG	3122801	Dom Viçoso
Brazil	31	MG	3122900	Dona Eusébia
Brazil	31	MG	3123007	Dores de Campos
Brazil	31	MG	3123106	Dores de Guanhães
Brazil	31	MG	3123205	Dores do Indaiá
Brazil	31	MG	3123304	Dores do Turvo
Brazil	31	MG	3123403	Doresópolis
Brazil	31	MG	3123502	Douradoquara
Brazil	31	MG	3123528	Durandé
Brazil	31	MG	3123601	Elói Mendes
Brazil	31	MG	3123700	Engenheiro Caldas
Brazil	31	MG	3123809	Engenheiro Navarro
Brazil	31	MG	3123858	Entre Folhas
Brazil	31	MG	3123908	Entre Rios de Minas
Brazil	31	MG	3124005	Ervália
Brazil	31	MG	3124104	Esmeraldas
Brazil	31	MG	3124203	Espera Feliz
Brazil	31	MG	3124302	Espinosa
Brazil	31	MG	3124401	Espírito Santo do Dourado
Brazil	31	MG	3124500	Estiva
Brazil	31	MG	3124609	Estrela Dalva
Brazil	31	MG	3124708	Estrela do Indaiá
Brazil	31	MG	3124807	Estrela do Sul
Brazil	31	MG	3124906	Eugenópolis
Brazil	31	MG	3125002	Ewbank da Câmara
Brazil	31	MG	3125101	Extrema
Brazil	31	MG	3125200	Fama
Brazil	31	MG	3125309	Faria Lemos
Brazil	31	MG	3125408	Felício dos Santos
Brazil	31	MG	3125606	Felisburgo
Brazil	31	MG	3125705	Felixlândia
Brazil	31	MG	3125804	Fernandes Tourinho
Brazil	31	MG	3125903	Ferros
Brazil	31	MG	3125952	Fervedouro
Brazil	31	MG	3126000	Florestal
Brazil	31	MG	3126109	Formiga
Brazil	31	MG	3126208	Formoso
Brazil	31	MG	3126307	Fortaleza de Minas
Brazil	31	MG	3126406	Fortuna de Minas
Brazil	31	MG	3126505	Francisco Badaró
Brazil	31	MG	3126604	Francisco Dumont
Brazil	31	MG	3126703	Francisco Sá
Brazil	31	MG	3126752	Franciscópolis
Brazil	31	MG	3126802	Frei Gaspar
Brazil	31	MG	3126901	Frei Inocêncio
Brazil	31	MG	3126950	Frei Lagonegro
Brazil	31	MG	3127008	Fronteira
Brazil	31	MG	3127057	Fronteira dos Vales
Brazil	31	MG	3127073	Fruta de Leite
Brazil	31	MG	3127107	Frutal
Brazil	31	MG	3127206	Funilândia
Brazil	31	MG	3127305	Galiléia
Brazil	31	MG	3127339	Gameleiras
Brazil	31	MG	3127354	Glaucilândia
Brazil	31	MG	3127370	Goiabeira
Brazil	31	MG	3127388	Goianá
Brazil	31	MG	3127404	Gonçalves
Brazil	31	MG	3127503	Gonzaga
Brazil	31	MG	3127602	Gouveia
Brazil	31	MG	3127701	Governador Valadares
Brazil	31	MG	3127800	Grão Mogol
Brazil	31	MG	3127909	Grupiara
Brazil	31	MG	3128006	Guanhães
Brazil	31	MG	3128105	Guapé
Brazil	31	MG	3128204	Guaraciaba
Brazil	31	MG	3128253	Guaraciama
Brazil	31	MG	3128303	Guaranésia
Brazil	31	MG	3128402	Guarani
Brazil	31	MG	3128501	Guarará
Brazil	31	MG	3128600	Guarda-Mor
Brazil	31	MG	3128709	Guaxupé
Brazil	31	MG	3128808	Guidoval
Brazil	31	MG	3128907	Guimarânia
Brazil	31	MG	3129004	Guiricema
Brazil	31	MG	3129103	Gurinhatã
Brazil	31	MG	3129202	Heliodora
Brazil	31	MG	3129301	Iapu
Brazil	31	MG	3129400	Ibertioga
Brazil	31	MG	3129509	Ibiá
Brazil	31	MG	3129608	Ibiaí
Brazil	31	MG	3129657	Ibiracatu
Brazil	31	MG	3129707	Ibiraci
Brazil	31	MG	3129806	Ibirité
Brazil	31	MG	3129905	Ibitiúra de Minas
Brazil	31	MG	3130002	Ibituruna
Brazil	31	MG	3130051	Icaraí de Minas
Brazil	31	MG	3130101	Igarapé
Brazil	31	MG	3130200	Igaratinga
Brazil	31	MG	3130309	Iguatama
Brazil	31	MG	3130408	Ijaci
Brazil	31	MG	3130507	Ilicínea
Brazil	31	MG	3130556	Imbé de Minas
Brazil	31	MG	3130606	Inconfidentes
Brazil	31	MG	3130655	Indaiabira
Brazil	31	MG	3130705	Indianópolis
Brazil	31	MG	3130804	Ingaí
Brazil	31	MG	3130903	Inhapim
Brazil	31	MG	3131000	Inhaúma
Brazil	31	MG	3131109	Inimutaba
Brazil	31	MG	3131158	Ipaba
Brazil	31	MG	3131208	Ipanema
Brazil	31	MG	3131307	Ipatinga
Brazil	31	MG	3131406	Ipiaçu
Brazil	31	MG	3131505	Ipuiúna
Brazil	31	MG	3131604	Iraí de Minas
Brazil	31	MG	3131703	Itabira
Brazil	31	MG	3131802	Itabirinha
Brazil	31	MG	3131901	Itabirito
Brazil	31	MG	3132008	Itacambira
Brazil	31	MG	3132107	Itacarambi
Brazil	31	MG	3132206	Itaguara
Brazil	31	MG	3132305	Itaipé
Brazil	31	MG	3132404	Itajubá
Brazil	31	MG	3132503	Itamarandiba
Brazil	31	MG	3132602	Itamarati de Minas
Brazil	31	MG	3132701	Itambacuri
Brazil	31	MG	3132800	Itambé do Mato Dentro
Brazil	31	MG	3132909	Itamogi
Brazil	31	MG	3133006	Itamonte
Brazil	31	MG	3133105	Itanhandu
Brazil	31	MG	3133204	Itanhomi
Brazil	31	MG	3133303	Itaobim
Brazil	31	MG	3133402	Itapagipe
Brazil	31	MG	3133501	Itapecerica
Brazil	31	MG	3133600	Itapeva
Brazil	31	MG	3133709	Itatiaiuçu
Brazil	31	MG	3133758	Itaú de Minas
Brazil	31	MG	3133808	Itaúna
Brazil	31	MG	3133907	Itaverava
Brazil	31	MG	3134004	Itinga
Brazil	31	MG	3134103	Itueta
Brazil	31	MG	3134202	Ituiutaba
Brazil	31	MG	3134301	Itumirim
Brazil	31	MG	3134400	Iturama
Brazil	31	MG	3134509	Itutinga
Brazil	31	MG	3134608	Jaboticatubas
Brazil	31	MG	3134707	Jacinto
Brazil	31	MG	3134806	Jacuí
Brazil	31	MG	3134905	Jacutinga
Brazil	31	MG	3135001	Jaguaraçu
Brazil	31	MG	3135050	Jaíba
Brazil	31	MG	3135076	Jampruca
Brazil	31	MG	3135100	Janaúba
Brazil	31	MG	3135209	Januária
Brazil	31	MG	3135308	Japaraíba
Brazil	31	MG	3135357	Japonvar
Brazil	31	MG	3135407	Jeceaba
Brazil	31	MG	3135456	Jenipapo de Minas
Brazil	31	MG	3135506	Jequeri
Brazil	31	MG	3135605	Jequitaí
Brazil	31	MG	3135704	Jequitibá
Brazil	31	MG	3135803	Jequitinhonha
Brazil	31	MG	3135902	Jesuânia
Brazil	31	MG	3136009	Joaíma
Brazil	31	MG	3136108	Joanésia
Brazil	31	MG	3136207	João Monlevade
Brazil	31	MG	3136306	João Pinheiro
Brazil	31	MG	3136405	Joaquim Felício
Brazil	31	MG	3136504	Jordânia
Brazil	31	MG	3136520	José Gonçalves de Minas
Brazil	31	MG	3136553	José Raydan
Brazil	31	MG	3136579	Josenópolis
Brazil	31	MG	3136652	Juatuba
Brazil	31	MG	3136702	Juiz de Fora
Brazil	31	MG	3136801	Juramento
Brazil	31	MG	3136900	Juruaia
Brazil	31	MG	3136959	Juvenília
Brazil	31	MG	3137007	Ladainha
Brazil	31	MG	3137106	Lagamar
Brazil	31	MG	3137205	Lagoa da Prata
Brazil	31	MG	3137304	Lagoa dos Patos
Brazil	31	MG	3137403	Lagoa Dourada
Brazil	31	MG	3137502	Lagoa Formosa
Brazil	31	MG	3137536	Lagoa Grande
Brazil	31	MG	3137601	Lagoa Santa
Brazil	31	MG	3137700	Lajinha
Brazil	31	MG	3137809	Lambari
Brazil	31	MG	3137908	Lamim
Brazil	31	MG	3138005	Laranjal
Brazil	31	MG	3138104	Lassance
Brazil	31	MG	3138203	Lavras
Brazil	31	MG	3138302	Leandro Ferreira
Brazil	31	MG	3138351	Leme do Prado
Brazil	31	MG	3138401	Leopoldina
Brazil	31	MG	3138500	Liberdade
Brazil	31	MG	3138609	Lima Duarte
Brazil	31	MG	3138625	Limeira do Oeste
Brazil	31	MG	3138658	Lontra
Brazil	31	MG	3138674	Luisburgo
Brazil	31	MG	3138682	Luislândia
Brazil	31	MG	3138708	Luminárias
Brazil	31	MG	3138807	Luz
Brazil	31	MG	3138906	Machacalis
Brazil	31	MG	3139003	Machado
Brazil	31	MG	3139102	Madre de Deus de Minas
Brazil	31	MG	3139201	Malacacheta
Brazil	31	MG	3139250	Mamonas
Brazil	31	MG	3139300	Manga
Brazil	31	MG	3139409	Manhuaçu
Brazil	31	MG	3139508	Manhumirim
Brazil	31	MG	3139607	Mantena
Brazil	31	MG	3139805	Mar de Espanha
Brazil	31	MG	3139706	Maravilhas
Brazil	31	MG	3139904	Maria da Fé
Brazil	31	MG	3140001	Mariana
Brazil	31	MG	3140100	Marilac
Brazil	31	MG	3140159	Mário Campos
Brazil	31	MG	3140209	Maripá de Minas
Brazil	31	MG	3140308	Marliéria
Brazil	31	MG	3140407	Marmelópolis
Brazil	31	MG	3140506	Martinho Campos
Brazil	31	MG	3140530	Martins Soares
Brazil	31	MG	3140555	Mata Verde
Brazil	31	MG	3140605	Materlândia
Brazil	31	MG	3140704	Mateus Leme
Brazil	31	MG	3171501	Mathias Lobato
Brazil	31	MG	3140803	Matias Barbosa
Brazil	31	MG	3140852	Matias Cardoso
Brazil	31	MG	3140902	Matipó
Brazil	31	MG	3141009	Mato Verde
Brazil	31	MG	3141108	Matozinhos
Brazil	31	MG	3141207	Matutina
Brazil	31	MG	3141306	Medeiros
Brazil	31	MG	3141405	Medina
Brazil	31	MG	3141504	Mendes Pimentel
Brazil	31	MG	3141603	Mercês
Brazil	31	MG	3141702	Mesquita
Brazil	31	MG	3141801	Minas Novas
Brazil	31	MG	3141900	Minduri
Brazil	31	MG	3142007	Mirabela
Brazil	31	MG	3142106	Miradouro
Brazil	31	MG	3142205	Miraí
Brazil	31	MG	3142254	Miravânia
Brazil	31	MG	3142304	Moeda
Brazil	31	MG	3142403	Moema
Brazil	31	MG	3142502	Monjolos
Brazil	31	MG	3142601	Monsenhor Paulo
Brazil	31	MG	3142700	Montalvânia
Brazil	31	MG	3142809	Monte Alegre de Minas
Brazil	31	MG	3142908	Monte Azul
Brazil	31	MG	3143005	Monte Belo
Brazil	31	MG	3143104	Monte Carmelo
Brazil	31	MG	3143153	Monte Formoso
Brazil	31	MG	3143203	Monte Santo de Minas
Brazil	31	MG	3143401	Monte Sião
Brazil	31	MG	3143302	Montes Claros
Brazil	31	MG	3143450	Montezuma
Brazil	31	MG	3143500	Morada Nova de Minas
Brazil	31	MG	3143609	Morro da Garça
Brazil	31	MG	3143708	Morro do Pilar
Brazil	31	MG	3143807	Munhoz
Brazil	31	MG	3143906	Muriaé
Brazil	31	MG	3144003	Mutum
Brazil	31	MG	3144102	Muzambinho
Brazil	31	MG	3144201	Nacip Raydan
Brazil	31	MG	3144300	Nanuque
Brazil	31	MG	3144359	Naque
Brazil	31	MG	3144375	Natalândia
Brazil	31	MG	3144409	Natércia
Brazil	31	MG	3144508	Nazareno
Brazil	31	MG	3144607	Nepomuceno
Brazil	31	MG	3144656	Ninheira
Brazil	31	MG	3144672	Nova Belém
Brazil	31	MG	3144706	Nova Era
Brazil	31	MG	3144805	Nova Lima
Brazil	31	MG	3144904	Nova Módica
Brazil	31	MG	3145000	Nova Ponte
Brazil	31	MG	3145059	Nova Porteirinha
Brazil	31	MG	3145109	Nova Resende
Brazil	31	MG	3145208	Nova Serrana
Brazil	31	MG	3136603	Nova União
Brazil	31	MG	3145307	Novo Cruzeiro
Brazil	31	MG	3145356	Novo Oriente de Minas
Brazil	31	MG	3145372	Novorizonte
Brazil	31	MG	3145406	Olaria
Brazil	31	MG	3145455	Olhos-d'Água
Brazil	31	MG	3145505	Olímpio Noronha
Brazil	31	MG	3145604	Oliveira
Brazil	31	MG	3145703	Oliveira Fortes
Brazil	31	MG	3145802	Onça de Pitangui
Brazil	31	MG	3145851	Oratórios
Brazil	31	MG	3145877	Orizânia
Brazil	31	MG	3145901	Ouro Branco
Brazil	31	MG	3146008	Ouro Fino
Brazil	31	MG	3146107	Ouro Preto
Brazil	31	MG	3146206	Ouro Verde de Minas
Brazil	31	MG	3146255	Padre Carvalho
Brazil	31	MG	3146305	Padre Paraíso
Brazil	31	MG	3146552	Pai Pedro
Brazil	31	MG	3146404	Paineiras
Brazil	31	MG	3146503	Pains
Brazil	31	MG	3146602	Paiva
Brazil	31	MG	3146701	Palma
Brazil	31	MG	3146750	Palmópolis
Brazil	31	MG	3146909	Papagaios
Brazil	31	MG	3147105	Pará de Minas
Brazil	31	MG	3147006	Paracatu
Brazil	31	MG	3147204	Paraguaçu
Brazil	31	MG	3147303	Paraisópolis
Brazil	31	MG	3147402	Paraopeba
Brazil	31	MG	3147600	Passa Quatro
Brazil	31	MG	3147709	Passa Tempo
Brazil	31	MG	3147501	Passabém
Brazil	31	MG	3147808	Passa-Vinte
Brazil	31	MG	3147907	Passos
Brazil	31	MG	3147956	Patis
Brazil	31	MG	3148004	Patos de Minas
Brazil	31	MG	3148103	Patrocínio
Brazil	31	MG	3148202	Patrocínio do Muriaé
Brazil	31	MG	3148301	Paula Cândido
Brazil	31	MG	3148400	Paulistas
Brazil	31	MG	3148509	Pavão
Brazil	31	MG	3148608	Peçanha
Brazil	31	MG	3148707	Pedra Azul
Brazil	31	MG	3148756	Pedra Bonita
Brazil	31	MG	3148806	Pedra do Anta
Brazil	31	MG	3148905	Pedra do Indaiá
Brazil	31	MG	3149002	Pedra Dourada
Brazil	31	MG	3149101	Pedralva
Brazil	31	MG	3149150	Pedras de Maria da Cruz
Brazil	31	MG	3149200	Pedrinópolis
Brazil	31	MG	3149309	Pedro Leopoldo
Brazil	31	MG	3149408	Pedro Teixeira
Brazil	31	MG	3149507	Pequeri
Brazil	31	MG	3149606	Pequi
Brazil	31	MG	3149705	Perdigão
Brazil	31	MG	3149804	Perdizes
Brazil	31	MG	3149903	Perdões
Brazil	31	MG	3149952	Periquito
Brazil	31	MG	3150000	Pescador
Brazil	31	MG	3150109	Piau
Brazil	31	MG	3150158	Piedade de Caratinga
Brazil	31	MG	3150208	Piedade de Ponte Nova
Brazil	31	MG	3150307	Piedade do Rio Grande
Brazil	31	MG	3150406	Piedade dos Gerais
Brazil	31	MG	3150505	Pimenta
Brazil	31	MG	3150539	Pingo-d'Água
Brazil	31	MG	3150570	Pintópolis
Brazil	31	MG	3150604	Piracema
Brazil	31	MG	3150703	Pirajuba
Brazil	31	MG	3150802	Piranga
Brazil	31	MG	3150901	Piranguçu
Brazil	31	MG	3151008	Piranguinho
Brazil	31	MG	3151107	Pirapetinga
Brazil	31	MG	3151206	Pirapora
Brazil	31	MG	3151305	Piraúba
Brazil	31	MG	3151404	Pitangui
Brazil	31	MG	3151503	Piumhi
Brazil	31	MG	3151602	Planura
Brazil	31	MG	3151701	Poço Fundo
Brazil	31	MG	3151800	Poços de Caldas
Brazil	31	MG	3151909	Pocrane
Brazil	31	MG	3152006	Pompéu
Brazil	31	MG	3152105	Ponte Nova
Brazil	31	MG	3152131	Ponto Chique
Brazil	31	MG	3152170	Ponto dos Volantes
Brazil	31	MG	3152204	Porteirinha
Brazil	31	MG	3152303	Porto Firme
Brazil	31	MG	3152402	Poté
Brazil	31	MG	3152501	Pouso Alegre
Brazil	31	MG	3152600	Pouso Alto
Brazil	31	MG	3152709	Prados
Brazil	31	MG	3152808	Prata
Brazil	31	MG	3152907	Pratápolis
Brazil	31	MG	3153004	Pratinha
Brazil	31	MG	3153103	Presidente Bernardes
Brazil	31	MG	3153202	Presidente Juscelino
Brazil	31	MG	3153301	Presidente Kubitschek
Brazil	31	MG	3153400	Presidente Olegário
Brazil	31	MG	3153608	Prudente de Morais
Brazil	31	MG	3153707	Quartel Geral
Brazil	31	MG	3153806	Queluzito
Brazil	31	MG	3153905	Raposos
Brazil	31	MG	3154002	Raul Soares
Brazil	31	MG	3154101	Recreio
Brazil	31	MG	3154150	Reduto
Brazil	31	MG	3154200	Resende Costa
Brazil	31	MG	3154309	Resplendor
Brazil	31	MG	3154408	Ressaquinha
Brazil	31	MG	3154457	Riachinho
Brazil	31	MG	3154507	Riacho dos Machados
Brazil	31	MG	3154606	Ribeirão das Neves
Brazil	31	MG	3154705	Ribeirão Vermelho
Brazil	31	MG	3154804	Rio Acima
Brazil	31	MG	3154903	Rio Casca
Brazil	31	MG	3155108	Rio do Prado
Brazil	31	MG	3155009	Rio Doce
Brazil	31	MG	3155207	Rio Espera
Brazil	31	MG	3155306	Rio Manso
Brazil	31	MG	3155405	Rio Novo
Brazil	31	MG	3155504	Rio Paranaíba
Brazil	31	MG	3155603	Rio Pardo de Minas
Brazil	31	MG	3155702	Rio Piracicaba
Brazil	31	MG	3155801	Rio Pomba
Brazil	31	MG	3155900	Rio Preto
Brazil	31	MG	3156007	Rio Vermelho
Brazil	31	MG	3156106	Ritápolis
Brazil	31	MG	3156205	Rochedo de Minas
Brazil	31	MG	3156304	Rodeiro
Brazil	31	MG	3156403	Romaria
Brazil	31	MG	3156452	Rosário da Limeira
Brazil	31	MG	3156502	Rubelita
Brazil	31	MG	3156601	Rubim
Brazil	31	MG	3156700	Sabará
Brazil	31	MG	3156809	Sabinópolis
Brazil	31	MG	3156908	Sacramento
Brazil	31	MG	3157005	Salinas
Brazil	31	MG	3157104	Salto da Divisa
Brazil	31	MG	3157203	Santa Bárbara
Brazil	31	MG	3157252	Santa Bárbara do Leste
Brazil	31	MG	3157278	Santa Bárbara do Monte Verde
Brazil	31	MG	3157302	Santa Bárbara do Tugúrio
Brazil	31	MG	3157336	Santa Cruz de Minas
Brazil	31	MG	3157377	Santa Cruz de Salinas
Brazil	31	MG	3157401	Santa Cruz do Escalvado
Brazil	31	MG	3157500	Santa Efigênia de Minas
Brazil	31	MG	3157609	Santa Fé de Minas
Brazil	31	MG	3157658	Santa Helena de Minas
Brazil	31	MG	3157708	Santa Juliana
Brazil	31	MG	3157807	Santa Luzia
Brazil	31	MG	3157906	Santa Margarida
Brazil	31	MG	3158003	Santa Maria de Itabira
Brazil	31	MG	3158102	Santa Maria do Salto
Brazil	31	MG	3158201	Santa Maria do Suaçuí
Brazil	31	MG	3159209	Santa Rita de Caldas
Brazil	31	MG	3159407	Santa Rita de Ibitipoca
Brazil	31	MG	3159308	Santa Rita de Jacutinga
Brazil	31	MG	3159357	Santa Rita de Minas
Brazil	31	MG	3159506	Santa Rita do Itueto
Brazil	31	MG	3159605	Santa Rita do Sapucaí
Brazil	31	MG	3159704	Santa Rosa da Serra
Brazil	31	MG	3159803	Santa Vitória
Brazil	31	MG	3158300	Santana da Vargem
Brazil	31	MG	3158409	Santana de Cataguases
Brazil	31	MG	3158508	Santana de Pirapama
Brazil	31	MG	3158607	Santana do Deserto
Brazil	31	MG	3158706	Santana do Garambéu
Brazil	31	MG	3158805	Santana do Jacaré
Brazil	31	MG	3158904	Santana do Manhuaçu
Brazil	31	MG	3158953	Santana do Paraíso
Brazil	31	MG	3159001	Santana do Riacho
Brazil	31	MG	3159100	Santana dos Montes
Brazil	31	MG	3159902	Santo Antônio do Amparo
Brazil	31	MG	3160009	Santo Antônio do Aventureiro
Brazil	31	MG	3160108	Santo Antônio do Grama
Brazil	31	MG	3160207	Santo Antônio do Itambé
Brazil	31	MG	3160306	Santo Antônio do Jacinto
Brazil	31	MG	3160405	Santo Antônio do Monte
Brazil	31	MG	3160454	Santo Antônio do Retiro
Brazil	31	MG	3160504	Santo Antônio do Rio Abaixo
Brazil	31	MG	3160603	Santo Hipólito
Brazil	31	MG	3160702	Santos Dumont
Brazil	31	MG	3160801	São Bento Abade
Brazil	31	MG	3160900	São Brás do Suaçuí
Brazil	31	MG	3160959	São Domingos das Dores
Brazil	31	MG	3161007	São Domingos do Prata
Brazil	31	MG	3161056	São Félix de Minas
Brazil	31	MG	3161106	São Francisco
Brazil	31	MG	3161205	São Francisco de Paula
Brazil	31	MG	3161304	São Francisco de Sales
Brazil	31	MG	3161403	São Francisco do Glória
Brazil	31	MG	3161502	São Geraldo
Brazil	31	MG	3161601	São Geraldo da Piedade
Brazil	31	MG	3161650	São Geraldo do Baixio
Brazil	31	MG	3161700	São Gonçalo do Abaeté
Brazil	31	MG	3161809	São Gonçalo do Pará
Brazil	31	MG	3161908	São Gonçalo do Rio Abaixo
Brazil	31	MG	3125507	São Gonçalo do Rio Preto
Brazil	31	MG	3162005	São Gonçalo do Sapucaí
Brazil	31	MG	3162104	São Gotardo
Brazil	31	MG	3162203	São João Batista do Glória
Brazil	31	MG	3162252	São João da Lagoa
Brazil	31	MG	3162302	São João da Mata
Brazil	31	MG	3162401	São João da Ponte
Brazil	31	MG	3162450	São João das Missões
Brazil	31	MG	3162500	São João del Rei
Brazil	31	MG	3162559	São João do Manhuaçu
Brazil	31	MG	3162575	São João do Manteninha
Brazil	31	MG	3162609	São João do Oriente
Brazil	31	MG	3162658	São João do Pacuí
Brazil	31	MG	3162708	São João do Paraíso
Brazil	31	MG	3162807	São João Evangelista
Brazil	31	MG	3162906	São João Nepomuceno
Brazil	31	MG	3162922	São Joaquim de Bicas
Brazil	31	MG	3162948	São José da Barra
Brazil	31	MG	3162955	São José da Lapa
Brazil	31	MG	3163003	São José da Safira
Brazil	31	MG	3163102	São José da Varginha
Brazil	31	MG	3163201	São José do Alegre
Brazil	31	MG	3163300	São José do Divino
Brazil	31	MG	3163409	São José do Goiabal
Brazil	31	MG	3163508	São José do Jacuri
Brazil	31	MG	3163607	São José do Mantimento
Brazil	31	MG	3163706	São Lourenço
Brazil	31	MG	3163805	São Miguel do Anta
Brazil	31	MG	3163904	São Pedro da União
Brazil	31	MG	3164100	São Pedro do Suaçuí
Brazil	31	MG	3164001	São Pedro dos Ferros
Brazil	31	MG	3164209	São Romão
Brazil	31	MG	3164308	São Roque de Minas
Brazil	31	MG	3164407	São Sebastião da Bela Vista
Brazil	31	MG	3164431	São Sebastião da Vargem Alegre
Brazil	31	MG	3164472	São Sebastião do Anta
Brazil	31	MG	3164506	São Sebastião do Maranhão
Brazil	31	MG	3164605	São Sebastião do Oeste
Brazil	31	MG	3164704	São Sebastião do Paraíso
Brazil	31	MG	3164803	São Sebastião do Rio Preto
Brazil	31	MG	3164902	São Sebastião do Rio Verde
Brazil	31	MG	3165206	São Thomé das Letras
Brazil	31	MG	3165008	São Tiago
Brazil	31	MG	3165107	São Tomás de Aquino
Brazil	31	MG	3165305	São Vicente de Minas
Brazil	31	MG	3165404	Sapucaí-Mirim
Brazil	31	MG	3165503	Sardoá
Brazil	31	MG	3165537	Sarzedo
Brazil	31	MG	3165560	Sem-Peixe
Brazil	31	MG	3165578	Senador Amaral
Brazil	31	MG	3165602	Senador Cortes
Brazil	31	MG	3165701	Senador Firmino
Brazil	31	MG	3165800	Senador José Bento
Brazil	31	MG	3165909	Senador Modestino Gonçalves
Brazil	31	MG	3166006	Senhora de Oliveira
Brazil	31	MG	3166105	Senhora do Porto
Brazil	31	MG	3166204	Senhora dos Remédios
Brazil	31	MG	3166303	Sericita
Brazil	31	MG	3166402	Seritinga
Brazil	31	MG	3166501	Serra Azul de Minas
Brazil	31	MG	3166600	Serra da Saudade
Brazil	31	MG	3166808	Serra do Salitre
Brazil	31	MG	3166709	Serra dos Aimorés
Brazil	31	MG	3166907	Serrania
Brazil	31	MG	3166956	Serranópolis de Minas
Brazil	31	MG	3167004	Serranos
Brazil	31	MG	3167103	Serro
Brazil	31	MG	3167202	Sete Lagoas
Brazil	31	MG	3165552	Setubinha
Brazil	31	MG	3167301	Silveirânia
Brazil	31	MG	3167400	Silvianópolis
Brazil	31	MG	3167509	Simão Pereira
Brazil	31	MG	3167608	Simonésia
Brazil	31	MG	3167707	Sobrália
Brazil	31	MG	3167806	Soledade de Minas
Brazil	31	MG	3167905	Tabuleiro
Brazil	31	MG	3168002	Taiobeiras
Brazil	31	MG	3168051	Taparuba
Brazil	31	MG	3168101	Tapira
Brazil	31	MG	3168200	Tapiraí
Brazil	31	MG	3168309	Taquaraçu de Minas
Brazil	31	MG	3168408	Tarumirim
Brazil	31	MG	3168507	Teixeiras
Brazil	31	MG	3168606	Teófilo Otoni
Brazil	31	MG	3168705	Timóteo
Brazil	31	MG	3168804	Tiradentes
Brazil	31	MG	3168903	Tiros
Brazil	31	MG	3169000	Tocantins
Brazil	31	MG	3169059	Tocos do Moji
Brazil	31	MG	3169109	Toledo
Brazil	31	MG	3169208	Tombos
Brazil	31	MG	3169307	Três Corações
Brazil	31	MG	3169356	Três Marias
Brazil	31	MG	3169406	Três Pontas
Brazil	31	MG	3169505	Tumiritinga
Brazil	31	MG	3169604	Tupaciguara
Brazil	31	MG	3169703	Turmalina
Brazil	31	MG	3169802	Turvolândia
Brazil	31	MG	3169901	Ubá
Brazil	31	MG	3170008	Ubaí
Brazil	31	MG	3170057	Ubaporanga
Brazil	31	MG	3170107	Uberaba
Brazil	31	MG	3170206	Uberlândia
Brazil	31	MG	3170305	Umburatiba
Brazil	31	MG	3170404	Unaí
Brazil	31	MG	3170438	União de Minas
Brazil	31	MG	3170479	Uruana de Minas
Brazil	31	MG	3170503	Urucânia
Brazil	31	MG	3170529	Urucuia
Brazil	31	MG	3170578	Vargem Alegre
Brazil	31	MG	3170602	Vargem Bonita
Brazil	31	MG	3170651	Vargem Grande do Rio Pardo
Brazil	31	MG	3170701	Varginha
Brazil	31	MG	3170750	Varjão de Minas
Brazil	31	MG	3170800	Várzea da Palma
Brazil	31	MG	3170909	Varzelândia
Brazil	31	MG	3171006	Vazante
Brazil	31	MG	3171030	Verdelândia
Brazil	31	MG	3171071	Veredinha
Brazil	31	MG	3171105	Veríssimo
Brazil	31	MG	3171154	Vermelho Novo
Brazil	31	MG	3171204	Vespasiano
Brazil	31	MG	3171303	Viçosa
Brazil	31	MG	3171402	Vieiras
Brazil	31	MG	3171600	Virgem da Lapa
Brazil	31	MG	3171709	Virgínia
Brazil	31	MG	3171808	Virginópolis
Brazil	31	MG	3171907	Virgolândia
Brazil	31	MG	3172004	Visconde do Rio Branco
Brazil	31	MG	3172103	Volta Grande
Brazil	31	MG	3172202	Wenceslau Braz
\.
