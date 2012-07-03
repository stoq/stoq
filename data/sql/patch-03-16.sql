-- Remove te_created and te_modified from city_location
-- as they are not needed anymore
ALTER TABLE city_location DROP CONSTRAINT city_location_te_created_id_fkey;
ALTER TABLE city_location DROP CONSTRAINT city_location_te_modified_id_fkey;
DELETE FROM transaction_entry t USING city_location c
    WHERE c.te_created_id = t.id or c.te_modified_id = t.id;
ALTER TABLE city_location DROP COLUMN te_created_id;
ALTER TABLE city_location DROP COLUMN te_modified_id;

-- Add state_code and city_code to city_location table
ALTER TABLE city_location ADD COLUMN city_code integer;
ALTER TABLE city_location ADD COLUMN state_code integer;

-- We are using __BRA__ here to avoid problems with UNIQUE constraints,
-- as for sure we will have a lot of those cities already registered.
-- All data will be fixed the right way on the next patch.
-- This data was adapted from:
--     http://www.sped.fazenda.gov.br/spedtabelas/AppConsulta/publico/aspx/ConsultaTabelasExternas.aspx?CodSistema=SpedFiscal
COPY city_location
(country, state_code, state, city_code, city) FROM stdin;
__BRA__	53	DF	5300108	Brasília
__BRA__	14	RR	1400050	Alto Alegre
__BRA__	14	RR	1400027	Amajari
__BRA__	14	RR	1400100	Boa Vista
__BRA__	14	RR	1400159	Bonfim
__BRA__	14	RR	1400175	Cantá
__BRA__	14	RR	1400209	Caracaraí
__BRA__	14	RR	1400233	Caroebe
__BRA__	14	RR	1400282	Iracema
__BRA__	14	RR	1400308	Mucajaí
__BRA__	14	RR	1400407	Normandia
__BRA__	14	RR	1400456	Pacaraima
__BRA__	14	RR	1400472	Rorainópolis
__BRA__	14	RR	1400506	São João da Baliza
__BRA__	14	RR	1400605	São Luiz
__BRA__	14	RR	1400704	Uiramutã
__BRA__	16	AP	1600105	Amapá
__BRA__	16	AP	1600204	Calçoene
__BRA__	16	AP	1600212	Cutias
__BRA__	16	AP	1600238	Ferreira Gomes
__BRA__	16	AP	1600253	Itaubal
__BRA__	16	AP	1600279	Laranjal do Jari
__BRA__	16	AP	1600303	Macapá
__BRA__	16	AP	1600402	Mazagão
__BRA__	16	AP	1600501	Oiapoque
__BRA__	16	AP	1600154	Pedra Branca do Amapari
__BRA__	16	AP	1600535	Porto Grande
__BRA__	16	AP	1600550	Pracuúba
__BRA__	16	AP	1600600	Santana
__BRA__	16	AP	1600055	Serra do Navio
__BRA__	16	AP	1600709	Tartarugalzinho
__BRA__	16	AP	1600808	Vitória do Jari
__BRA__	12	AC	1200013	Acrelândia
__BRA__	12	AC	1200054	Assis Brasil
__BRA__	12	AC	1200104	Brasiléia
__BRA__	12	AC	1200138	Bujari
__BRA__	12	AC	1200179	Capixaba
__BRA__	12	AC	1200203	Cruzeiro do Sul
__BRA__	12	AC	1200252	Epitaciolândia
__BRA__	12	AC	1200302	Feijó
__BRA__	12	AC	1200328	Jordão
__BRA__	12	AC	1200336	Mâncio Lima
__BRA__	12	AC	1200344	Manoel Urbano
__BRA__	12	AC	1200351	Marechal Thaumaturgo
__BRA__	12	AC	1200385	Plácido de Castro
__BRA__	12	AC	1200807	Porto Acre
__BRA__	12	AC	1200393	Porto Walter
__BRA__	12	AC	1200401	Rio Branco
__BRA__	12	AC	1200427	Rodrigues Alves
__BRA__	12	AC	1200435	Santa Rosa do Purus
__BRA__	12	AC	1200500	Sena Madureira
__BRA__	12	AC	1200450	Senador Guiomard
__BRA__	12	AC	1200609	Tarauacá
__BRA__	12	AC	1200708	Xapuri
__BRA__	11	RO	1100015	Alta Floresta D'Oeste
__BRA__	11	RO	1100379	Alto Alegre dos Parecis
__BRA__	11	RO	1100403	Alto Paraíso
__BRA__	11	RO	1100346	Alvorada D'Oeste
__BRA__	11	RO	1100023	Ariquemes
__BRA__	11	RO	1100452	Buritis
__BRA__	11	RO	1100031	Cabixi
__BRA__	11	RO	1100601	Cacaulândia
__BRA__	11	RO	1100049	Cacoal
__BRA__	11	RO	1100700	Campo Novo de Rondônia
__BRA__	11	RO	1100809	Candeias do Jamari
__BRA__	11	RO	1100908	Castanheiras
__BRA__	11	RO	1100056	Cerejeiras
__BRA__	11	RO	1100924	Chupinguaia
__BRA__	11	RO	1100064	Colorado do Oeste
__BRA__	11	RO	1100072	Corumbiara
__BRA__	11	RO	1100080	Costa Marques
__BRA__	11	RO	1100940	Cujubim
__BRA__	11	RO	1100098	Espigão D'Oeste
__BRA__	11	RO	1101005	Governador Jorge Teixeira
__BRA__	11	RO	1100106	Guajará-Mirim
__BRA__	11	RO	1101104	Itapuã do Oeste
__BRA__	11	RO	1100114	Jaru
__BRA__	11	RO	1100122	Ji-Paraná
__BRA__	11	RO	1100130	Machadinho D'Oeste
__BRA__	11	RO	1101203	Ministro Andreazza
__BRA__	11	RO	1101302	Mirante da Serra
__BRA__	11	RO	1101401	Monte Negro
__BRA__	11	RO	1100148	Nova Brasilândia D'Oeste
__BRA__	11	RO	1100338	Nova Mamoré
__BRA__	11	RO	1101435	Nova União
__BRA__	11	RO	1100502	Novo Horizonte do Oeste
__BRA__	11	RO	1100155	Ouro Preto do Oeste
__BRA__	11	RO	1101450	Parecis
__BRA__	11	RO	1100189	Pimenta Bueno
__BRA__	11	RO	1101468	Pimenteiras do Oeste
__BRA__	11	RO	1100205	Porto Velho
__BRA__	11	RO	1100254	Presidente Médici
__BRA__	11	RO	1101476	Primavera de Rondônia
__BRA__	11	RO	1100262	Rio Crespo
__BRA__	11	RO	1100288	Rolim de Moura
__BRA__	11	RO	1100296	Santa Luzia D'Oeste
__BRA__	11	RO	1101484	São Felipe D'Oeste
__BRA__	11	RO	1101492	São Francisco do Guaporé
__BRA__	11	RO	1100320	São Miguel do Guaporé
__BRA__	11	RO	1101500	Seringueiras
__BRA__	11	RO	1101559	Teixeirópolis
__BRA__	11	RO	1101609	Theobroma
__BRA__	11	RO	1101708	Urupá
__BRA__	11	RO	1101757	Vale do Anari
__BRA__	11	RO	1101807	Vale do Paraíso
__BRA__	11	RO	1100304	Vilhena
__BRA__	13	AM	1300029	Alvarães
__BRA__	13	AM	1300060	Amaturá
__BRA__	13	AM	1300086	Anamã
__BRA__	13	AM	1300102	Anori
__BRA__	13	AM	1300144	Apuí
__BRA__	13	AM	1300201	Atalaia do Norte
__BRA__	13	AM	1300300	Autazes
__BRA__	13	AM	1300409	Barcelos
__BRA__	13	AM	1300508	Barreirinha
__BRA__	13	AM	1300607	Benjamin Constant
__BRA__	13	AM	1300631	Beruri
__BRA__	13	AM	1300680	Boa Vista do Ramos
__BRA__	13	AM	1300706	Boca do Acre
__BRA__	13	AM	1300805	Borba
__BRA__	13	AM	1300839	Caapiranga
__BRA__	13	AM	1300904	Canutama
__BRA__	13	AM	1301001	Carauari
__BRA__	13	AM	1301100	Careiro
__BRA__	13	AM	1301159	Careiro da Várzea
__BRA__	13	AM	1301209	Coari
__BRA__	13	AM	1301308	Codajás
__BRA__	13	AM	1301407	Eirunepé
__BRA__	13	AM	1301506	Envira
__BRA__	13	AM	1301605	Fonte Boa
__BRA__	13	AM	1301654	Guajará
__BRA__	13	AM	1301704	Humaitá
__BRA__	13	AM	1301803	Ipixuna
__BRA__	13	AM	1301852	Iranduba
__BRA__	13	AM	1301902	Itacoatiara
__BRA__	13	AM	1301951	Itamarati
__BRA__	13	AM	1302009	Itapiranga
__BRA__	13	AM	1302108	Japurá
__BRA__	13	AM	1302207	Juruá
__BRA__	13	AM	1302306	Jutaí
__BRA__	13	AM	1302405	Lábrea
__BRA__	13	AM	1302504	Manacapuru
__BRA__	13	AM	1302553	Manaquiri
__BRA__	13	AM	1302603	Manaus
__BRA__	13	AM	1302702	Manicoré
__BRA__	13	AM	1302801	Maraã
__BRA__	13	AM	1302900	Maués
__BRA__	13	AM	1303007	Nhamundá
__BRA__	13	AM	1303106	Nova Olinda do Norte
__BRA__	13	AM	1303205	Novo Airão
__BRA__	13	AM	1303304	Novo Aripuanã
__BRA__	13	AM	1303403	Parintins
__BRA__	13	AM	1303502	Pauini
__BRA__	13	AM	1303536	Presidente Figueiredo
__BRA__	13	AM	1303569	Rio Preto da Eva
__BRA__	13	AM	1303601	Santa Isabel do Rio Negro
__BRA__	13	AM	1303700	Santo Antônio do Içá
__BRA__	13	AM	1303809	São Gabriel da Cachoeira
__BRA__	13	AM	1303908	São Paulo de Olivença
__BRA__	13	AM	1303957	São Sebastião do Uatumã
__BRA__	13	AM	1304005	Silves
__BRA__	13	AM	1304062	Tabatinga
__BRA__	13	AM	1304104	Tapauá
__BRA__	13	AM	1304203	Tefé
__BRA__	13	AM	1304237	Tonantins
__BRA__	13	AM	1304260	Uarini
__BRA__	13	AM	1304302	Urucará
__BRA__	13	AM	1304401	Urucurituba
__BRA__	28	SE	2800100	Amparo de São Francisco
__BRA__	28	SE	2800209	Aquidabã
__BRA__	28	SE	2800308	Aracaju
__BRA__	28	SE	2800407	Arauá
__BRA__	28	SE	2800506	Areia Branca
__BRA__	28	SE	2800605	Barra dos Coqueiros
__BRA__	28	SE	2800670	Boquim
__BRA__	28	SE	2800704	Brejo Grande
__BRA__	28	SE	2801009	Campo do Brito
__BRA__	28	SE	2801108	Canhoba
__BRA__	28	SE	2801207	Canindé de São Francisco
__BRA__	28	SE	2801306	Capela
__BRA__	28	SE	2801405	Carira
__BRA__	28	SE	2801504	Carmópolis
__BRA__	28	SE	2801603	Cedro de São João
__BRA__	28	SE	2801702	Cristinápolis
__BRA__	28	SE	2801900	Cumbe
__BRA__	28	SE	2802007	Divina Pastora
__BRA__	28	SE	2802106	Estância
__BRA__	28	SE	2802205	Feira Nova
__BRA__	28	SE	2802304	Frei Paulo
__BRA__	28	SE	2802403	Gararu
__BRA__	28	SE	2802502	General Maynard
__BRA__	28	SE	2802601	Gracho Cardoso
__BRA__	28	SE	2802700	Ilha das Flores
__BRA__	28	SE	2802809	Indiaroba
__BRA__	28	SE	2802908	Itabaiana
__BRA__	28	SE	2803005	Itabaianinha
__BRA__	28	SE	2803104	Itabi
__BRA__	28	SE	2803203	Itaporanga d'Ajuda
__BRA__	28	SE	2803302	Japaratuba
__BRA__	28	SE	2803401	Japoatã
__BRA__	28	SE	2803500	Lagarto
__BRA__	28	SE	2803609	Laranjeiras
__BRA__	28	SE	2803708	Macambira
__BRA__	28	SE	2803807	Malhada dos Bois
__BRA__	28	SE	2803906	Malhador
__BRA__	28	SE	2804003	Maruim
__BRA__	28	SE	2804102	Moita Bonita
__BRA__	28	SE	2804201	Monte Alegre de Sergipe
__BRA__	28	SE	2804300	Muribeca
__BRA__	28	SE	2804409	Neópolis
__BRA__	28	SE	2804458	Nossa Senhora Aparecida
__BRA__	28	SE	2804508	Nossa Senhora da Glória
__BRA__	28	SE	2804607	Nossa Senhora das Dores
__BRA__	28	SE	2804706	Nossa Senhora de Lourdes
__BRA__	28	SE	2804805	Nossa Senhora do Socorro
__BRA__	28	SE	2804904	Pacatuba
__BRA__	28	SE	2805000	Pedra Mole
__BRA__	28	SE	2805109	Pedrinhas
__BRA__	28	SE	2805208	Pinhão
__BRA__	28	SE	2805307	Pirambu
__BRA__	28	SE	2805406	Poço Redondo
__BRA__	28	SE	2805505	Poço Verde
__BRA__	28	SE	2805604	Porto da Folha
__BRA__	28	SE	2805703	Propriá
__BRA__	28	SE	2805802	Riachão do Dantas
__BRA__	28	SE	2805901	Riachuelo
__BRA__	28	SE	2806008	Ribeirópolis
__BRA__	28	SE	2806107	Rosário do Catete
__BRA__	28	SE	2806206	Salgado
__BRA__	28	SE	2806305	Santa Luzia do Itanhy
__BRA__	28	SE	2806503	Santa Rosa de Lima
__BRA__	28	SE	2806404	Santana do São Francisco
__BRA__	28	SE	2806602	Santo Amaro das Brotas
__BRA__	28	SE	2806701	São Cristóvão
__BRA__	28	SE	2806800	São Domingos
__BRA__	28	SE	2806909	São Francisco
__BRA__	28	SE	2807006	São Miguel do Aleixo
__BRA__	28	SE	2807105	Simão Dias
__BRA__	28	SE	2807204	Siriri
__BRA__	28	SE	2807303	Telha
__BRA__	28	SE	2807402	Tobias Barreto
__BRA__	28	SE	2807501	Tomar do Geru
__BRA__	28	SE	2807600	Umbaúba
__BRA__	32	ES	3200102	Afonso Cláudio
__BRA__	32	ES	3200169	Água Doce do Norte
__BRA__	32	ES	3200136	Águia Branca
__BRA__	32	ES	3200201	Alegre
__BRA__	32	ES	3200300	Alfredo Chaves
__BRA__	32	ES	3200359	Alto Rio Novo
__BRA__	32	ES	3200409	Anchieta
__BRA__	32	ES	3200508	Apiacá
__BRA__	32	ES	3200607	Aracruz
__BRA__	32	ES	3200706	Atilio Vivacqua
__BRA__	32	ES	3200805	Baixo Guandu
__BRA__	32	ES	3200904	Barra de São Francisco
__BRA__	32	ES	3201001	Boa Esperança
__BRA__	32	ES	3201100	Bom Jesus do Norte
__BRA__	32	ES	3201159	Brejetuba
__BRA__	32	ES	3201209	Cachoeiro de Itapemirim
__BRA__	32	ES	3201308	Cariacica
__BRA__	32	ES	3201407	Castelo
__BRA__	32	ES	3201506	Colatina
__BRA__	32	ES	3201605	Conceição da Barra
__BRA__	32	ES	3201704	Conceição do Castelo
__BRA__	32	ES	3201803	Divino de São Lourenço
__BRA__	32	ES	3201902	Domingos Martins
__BRA__	32	ES	3202009	Dores do Rio Preto
__BRA__	32	ES	3202108	Ecoporanga
__BRA__	32	ES	3202207	Fundão
__BRA__	32	ES	3202256	Governador Lindenberg
__BRA__	32	ES	3202306	Guaçuí
__BRA__	32	ES	3202405	Guarapari
__BRA__	32	ES	3202454	Ibatiba
__BRA__	32	ES	3202504	Ibiraçu
__BRA__	32	ES	3202553	Ibitirama
__BRA__	32	ES	3202603	Iconha
__BRA__	32	ES	3202652	Irupi
__BRA__	32	ES	3202702	Itaguaçu
__BRA__	32	ES	3202801	Itapemirim
__BRA__	32	ES	3202900	Itarana
__BRA__	32	ES	3203007	Iúna
__BRA__	32	ES	3203056	Jaguaré
__BRA__	32	ES	3203106	Jerônimo Monteiro
__BRA__	32	ES	3203130	João Neiva
__BRA__	32	ES	3203163	Laranja da Terra
__BRA__	32	ES	3203205	Linhares
__BRA__	32	ES	3203304	Mantenópolis
__BRA__	32	ES	3203320	Marataízes
__BRA__	32	ES	3203346	Marechal Floriano
__BRA__	32	ES	3203353	Marilândia
__BRA__	32	ES	3203403	Mimoso do Sul
__BRA__	32	ES	3203502	Montanha
__BRA__	32	ES	3203601	Mucurici
__BRA__	32	ES	3203700	Muniz Freire
__BRA__	32	ES	3203809	Muqui
__BRA__	32	ES	3203908	Nova Venécia
__BRA__	32	ES	3204005	Pancas
__BRA__	32	ES	3204054	Pedro Canário
__BRA__	32	ES	3204104	Pinheiros
__BRA__	32	ES	3204203	Piúma
__BRA__	32	ES	3204252	Ponto Belo
__BRA__	32	ES	3204302	Presidente Kennedy
__BRA__	32	ES	3204351	Rio Bananal
__BRA__	32	ES	3204401	Rio Novo do Sul
__BRA__	32	ES	3204500	Santa Leopoldina
__BRA__	32	ES	3204559	Santa Maria de Jetibá
__BRA__	32	ES	3204609	Santa Teresa
__BRA__	32	ES	3204658	São Domingos do Norte
__BRA__	32	ES	3204708	São Gabriel da Palha
__BRA__	32	ES	3204807	São José do Calçado
__BRA__	32	ES	3204906	São Mateus
__BRA__	32	ES	3204955	São Roque do Canaã
__BRA__	32	ES	3205002	Serra
__BRA__	32	ES	3205010	Sooretama
__BRA__	32	ES	3205036	Vargem Alta
__BRA__	32	ES	3205069	Venda Nova do Imigrante
__BRA__	32	ES	3205101	Viana
__BRA__	32	ES	3205150	Vila Pavão
__BRA__	32	ES	3205176	Vila Valério
__BRA__	32	ES	3205200	Vila Velha
__BRA__	32	ES	3205309	Vitória
__BRA__	50	MS	5000203	Água Clara
__BRA__	50	MS	5000252	Alcinópolis
__BRA__	50	MS	5000609	Amambaí
__BRA__	50	MS	5000708	Anastácio
__BRA__	50	MS	5000807	Anaurilândia
__BRA__	50	MS	5000856	Angélica
__BRA__	50	MS	5000906	Antônio João
__BRA__	50	MS	5001003	Aparecida do Taboado
__BRA__	50	MS	5001102	Aquidauana
__BRA__	50	MS	5001243	Aral Moreira
__BRA__	50	MS	5001508	Bandeirantes
__BRA__	50	MS	5001904	Bataguassu
__BRA__	50	MS	5002001	Batayporã
__BRA__	50	MS	5002100	Bela Vista
__BRA__	50	MS	5002159	Bodoquena
__BRA__	50	MS	5002209	Bonito
__BRA__	50	MS	5002308	Brasilândia
__BRA__	50	MS	5002407	Caarapó
__BRA__	50	MS	5002605	Camapuã
__BRA__	50	MS	5002704	Campo Grande
__BRA__	50	MS	5002803	Caracol
__BRA__	50	MS	5002902	Cassilândia
__BRA__	50	MS	5002951	Chapadão do Sul
__BRA__	50	MS	5003108	Corguinho
__BRA__	50	MS	5003157	Coronel Sapucaia
__BRA__	50	MS	5003207	Corumbá
__BRA__	50	MS	5003256	Costa Rica
__BRA__	50	MS	5003306	Coxim
__BRA__	50	MS	5003454	Deodápolis
__BRA__	50	MS	5003488	Dois Irmãos do Buriti
__BRA__	50	MS	5003504	Douradina
__BRA__	50	MS	5003702	Dourados
__BRA__	50	MS	5003751	Eldorado
__BRA__	50	MS	5003801	Fátima do Sul
__BRA__	50	MS	5003900	Figueirão
__BRA__	50	MS	5004007	Glória de Dourados
__BRA__	50	MS	5004106	Guia Lopes da Laguna
__BRA__	50	MS	5004304	Iguatemi
__BRA__	50	MS	5004403	Inocência
__BRA__	50	MS	5004502	Itaporã
__BRA__	50	MS	5004601	Itaquiraí
__BRA__	50	MS	5004700	Ivinhema
__BRA__	50	MS	5004809	Japorã
__BRA__	50	MS	5004908	Jaraguari
__BRA__	50	MS	5005004	Jardim
__BRA__	50	MS	5005103	Jateí
__BRA__	50	MS	5005152	Juti
__BRA__	50	MS	5005202	Ladário
__BRA__	50	MS	5005251	Laguna Carapã
__BRA__	50	MS	5005400	Maracaju
__BRA__	50	MS	5005608	Miranda
__BRA__	50	MS	5005681	Mundo Novo
__BRA__	50	MS	5005707	Naviraí
__BRA__	50	MS	5005806	Nioaque
__BRA__	50	MS	5006002	Nova Alvorada do Sul
__BRA__	50	MS	5006200	Nova Andradina
__BRA__	50	MS	5006259	Novo Horizonte do Sul
__BRA__	50	MS	5006309	Paranaíba
__BRA__	50	MS	5006358	Paranhos
__BRA__	50	MS	5006408	Pedro Gomes
__BRA__	50	MS	5006606	Ponta Porã
__BRA__	50	MS	5006903	Porto Murtinho
__BRA__	50	MS	5007109	Ribas do Rio Pardo
__BRA__	50	MS	5007208	Rio Brilhante
__BRA__	50	MS	5007307	Rio Negro
__BRA__	50	MS	5007406	Rio Verde de Mato Grosso
__BRA__	50	MS	5007505	Rochedo
__BRA__	50	MS	5007554	Santa Rita do Pardo
__BRA__	50	MS	5007695	São Gabriel do Oeste
__BRA__	50	MS	5007802	Selvíria
__BRA__	50	MS	5007703	Sete Quedas
__BRA__	50	MS	5007901	Sidrolândia
__BRA__	50	MS	5007935	Sonora
__BRA__	50	MS	5007950	Tacuru
__BRA__	50	MS	5007976	Taquarussu
__BRA__	50	MS	5008008	Terenos
__BRA__	50	MS	5008305	Três Lagoas
__BRA__	50	MS	5008404	Vicentina
__BRA__	33	RJ	3300100	Angra dos Reis
__BRA__	33	RJ	3300159	Aperibé
__BRA__	33	RJ	3300209	Araruama
__BRA__	33	RJ	3300225	Areal
__BRA__	33	RJ	3300233	Armação dos Búzios
__BRA__	33	RJ	3300258	Arraial do Cabo
__BRA__	33	RJ	3300308	Barra do Piraí
__BRA__	33	RJ	3300407	Barra Mansa
__BRA__	33	RJ	3300456	Belford Roxo
__BRA__	33	RJ	3300506	Bom Jardim
__BRA__	33	RJ	3300605	Bom Jesus do Itabapoana
__BRA__	33	RJ	3300704	Cabo Frio
__BRA__	33	RJ	3300803	Cachoeiras de Macacu
__BRA__	33	RJ	3300902	Cambuci
__BRA__	33	RJ	3301009	Campos dos Goytacazes
__BRA__	33	RJ	3301108	Cantagalo
__BRA__	33	RJ	3300936	Carapebus
__BRA__	33	RJ	3301157	Cardoso Moreira
__BRA__	33	RJ	3301207	Carmo
__BRA__	33	RJ	3301306	Casimiro de Abreu
__BRA__	33	RJ	3300951	Comendador Levy Gasparian
__BRA__	33	RJ	3301405	Conceição de Macabu
__BRA__	33	RJ	3301504	Cordeiro
__BRA__	33	RJ	3301603	Duas Barras
__BRA__	33	RJ	3301702	Duque de Caxias
__BRA__	33	RJ	3301801	Engenheiro Paulo de Frontin
__BRA__	33	RJ	3301850	Guapimirim
__BRA__	33	RJ	3301876	Iguaba Grande
__BRA__	33	RJ	3301900	Itaboraí
__BRA__	33	RJ	3302007	Itaguaí
__BRA__	33	RJ	3302056	Italva
__BRA__	33	RJ	3302106	Itaocara
__BRA__	33	RJ	3302205	Itaperuna
__BRA__	33	RJ	3302254	Itatiaia
__BRA__	33	RJ	3302270	Japeri
__BRA__	33	RJ	3302304	Laje do Muriaé
__BRA__	33	RJ	3302403	Macaé
__BRA__	33	RJ	3302452	Macuco
__BRA__	33	RJ	3302502	Magé
__BRA__	33	RJ	3302601	Mangaratiba
__BRA__	33	RJ	3302700	Maricá
__BRA__	33	RJ	3302809	Mendes
__BRA__	33	RJ	3302858	Mesquita
__BRA__	33	RJ	3302908	Miguel Pereira
__BRA__	33	RJ	3303005	Miracema
__BRA__	33	RJ	3303104	Natividade
__BRA__	33	RJ	3303203	Nilópolis
__BRA__	33	RJ	3303302	Niterói
__BRA__	33	RJ	3303401	Nova Friburgo
__BRA__	33	RJ	3303500	Nova Iguaçu
__BRA__	33	RJ	3303609	Paracambi
__BRA__	33	RJ	3303708	Paraíba do Sul
__BRA__	33	RJ	3303807	Parati
__BRA__	33	RJ	3303856	Paty do Alferes
__BRA__	33	RJ	3303906	Petrópolis
__BRA__	33	RJ	3303955	Pinheiral
__BRA__	33	RJ	3304003	Piraí
__BRA__	33	RJ	3304102	Porciúncula
__BRA__	33	RJ	3304110	Porto Real
__BRA__	33	RJ	3304128	Quatis
__BRA__	33	RJ	3304144	Queimados
__BRA__	33	RJ	3304151	Quissamã
__BRA__	33	RJ	3304201	Resende
__BRA__	33	RJ	3304300	Rio Bonito
__BRA__	33	RJ	3304409	Rio Claro
__BRA__	33	RJ	3304508	Rio das Flores
__BRA__	33	RJ	3304524	Rio das Ostras
__BRA__	33	RJ	3304557	Rio de Janeiro
__BRA__	33	RJ	3304607	Santa Maria Madalena
__BRA__	33	RJ	3304706	Santo Antônio de Pádua
__BRA__	33	RJ	3304805	São Fidélis
__BRA__	33	RJ	3304755	São Francisco de Itabapoana
__BRA__	33	RJ	3304904	São Gonçalo
__BRA__	33	RJ	3305000	São João da Barra
__BRA__	33	RJ	3305109	São João de Meriti
__BRA__	33	RJ	3305133	São José de Ubá
__BRA__	33	RJ	3305158	São José do Vale do Rio Preto
__BRA__	33	RJ	3305208	São Pedro da Aldeia
__BRA__	33	RJ	3305307	São Sebastião do Alto
__BRA__	33	RJ	3305406	Sapucaia
__BRA__	33	RJ	3305505	Saquarema
__BRA__	33	RJ	3305554	Seropédica
__BRA__	33	RJ	3305604	Silva Jardim
__BRA__	33	RJ	3305703	Sumidouro
__BRA__	33	RJ	3305752	Tanguá
__BRA__	33	RJ	3305802	Teresópolis
__BRA__	33	RJ	3305901	Trajano de Morais
__BRA__	33	RJ	3306008	Três Rios
__BRA__	33	RJ	3306107	Valença
__BRA__	33	RJ	3306156	Varre-Sai
__BRA__	33	RJ	3306206	Vassouras
__BRA__	33	RJ	3306305	Volta Redonda
__BRA__	27	AL	2700102	Água Branca
__BRA__	27	AL	2700201	Anadia
__BRA__	27	AL	2700300	Arapiraca
__BRA__	27	AL	2700409	Atalaia
__BRA__	27	AL	2700508	Barra de Santo Antônio
__BRA__	27	AL	2700607	Barra de São Miguel
__BRA__	27	AL	2700706	Batalha
__BRA__	27	AL	2700805	Belém
__BRA__	27	AL	2700904	Belo Monte
__BRA__	27	AL	2701001	Boca da Mata
__BRA__	27	AL	2701100	Branquinha
__BRA__	27	AL	2701209	Cacimbinhas
__BRA__	27	AL	2701308	Cajueiro
__BRA__	27	AL	2701357	Campestre
__BRA__	27	AL	2701407	Campo Alegre
__BRA__	27	AL	2701506	Campo Grande
__BRA__	27	AL	2701605	Canapi
__BRA__	27	AL	2701704	Capela
__BRA__	27	AL	2701803	Carneiros
__BRA__	27	AL	2701902	Chã Preta
__BRA__	27	AL	2702009	Coité do Nóia
__BRA__	27	AL	2702108	Colônia Leopoldina
__BRA__	27	AL	2702207	Coqueiro Seco
__BRA__	27	AL	2702306	Coruripe
__BRA__	27	AL	2702355	Craíbas
__BRA__	27	AL	2702405	Delmiro Gouveia
__BRA__	27	AL	2702504	Dois Riachos
__BRA__	27	AL	2702553	Estrela de Alagoas
__BRA__	27	AL	2702603	Feira Grande
__BRA__	27	AL	2702702	Feliz Deserto
__BRA__	27	AL	2702801	Flexeiras
__BRA__	27	AL	2702900	Girau do Ponciano
__BRA__	27	AL	2703007	Ibateguara
__BRA__	27	AL	2703106	Igaci
__BRA__	27	AL	2703205	Igreja Nova
__BRA__	27	AL	2703304	Inhapi
__BRA__	27	AL	2703403	Jacaré dos Homens
__BRA__	27	AL	2703502	Jacuípe
__BRA__	27	AL	2703601	Japaratinga
__BRA__	27	AL	2703700	Jaramataia
__BRA__	27	AL	2703759	Jequiá da Praia
__BRA__	27	AL	2703809	Joaquim Gomes
__BRA__	27	AL	2703908	Jundiá
__BRA__	27	AL	2704005	Junqueiro
__BRA__	27	AL	2704104	Lagoa da Canoa
__BRA__	27	AL	2704203	Limoeiro de Anadia
__BRA__	27	AL	2704302	Maceió
__BRA__	27	AL	2704401	Major Isidoro
__BRA__	27	AL	2704906	Mar Vermelho
__BRA__	27	AL	2704500	Maragogi
__BRA__	27	AL	2704609	Maravilha
__BRA__	27	AL	2704708	Marechal Deodoro
__BRA__	27	AL	2704807	Maribondo
__BRA__	27	AL	2705002	Mata Grande
__BRA__	27	AL	2705101	Matriz de Camaragibe
__BRA__	27	AL	2705200	Messias
__BRA__	27	AL	2705309	Minador do Negrão
__BRA__	27	AL	2705408	Monteirópolis
__BRA__	27	AL	2705507	Murici
__BRA__	27	AL	2705606	Novo Lino
__BRA__	27	AL	2705705	Olho d'Água das Flores
__BRA__	27	AL	2705804	Olho d'Água do Casado
__BRA__	27	AL	2705903	Olho d'Água Grande
__BRA__	27	AL	2706000	Olivença
__BRA__	27	AL	2706109	Ouro Branco
__BRA__	27	AL	2706208	Palestina
__BRA__	27	AL	2706307	Palmeira dos Índios
__BRA__	27	AL	2706406	Pão de Açúcar
__BRA__	27	AL	2706422	Pariconha
__BRA__	27	AL	2706448	Paripueira
__BRA__	27	AL	2706505	Passo de Camaragibe
__BRA__	27	AL	2706604	Paulo Jacinto
__BRA__	27	AL	2706703	Penedo
__BRA__	27	AL	2706802	Piaçabuçu
__BRA__	27	AL	2706901	Pilar
__BRA__	27	AL	2707008	Pindoba
__BRA__	27	AL	2707107	Piranhas
__BRA__	27	AL	2707206	Poço das Trincheiras
__BRA__	27	AL	2707305	Porto Calvo
__BRA__	27	AL	2707404	Porto de Pedras
__BRA__	27	AL	2707503	Porto Real do Colégio
__BRA__	27	AL	2707602	Quebrangulo
__BRA__	27	AL	2707701	Rio Largo
__BRA__	27	AL	2707800	Roteiro
__BRA__	27	AL	2707909	Santa Luzia do Norte
__BRA__	27	AL	2708006	Santana do Ipanema
__BRA__	27	AL	2708105	Santana do Mundaú
__BRA__	27	AL	2708204	São Brás
__BRA__	27	AL	2708303	São José da Laje
__BRA__	27	AL	2708402	São José da Tapera
__BRA__	27	AL	2708501	São Luís do Quitunde
__BRA__	27	AL	2708600	São Miguel dos Campos
__BRA__	27	AL	2708709	São Miguel dos Milagres
__BRA__	27	AL	2708808	São Sebastião
__BRA__	27	AL	2708907	Satuba
__BRA__	27	AL	2708956	Senador Rui Palmeira
__BRA__	27	AL	2709004	Tanque d'Arca
__BRA__	27	AL	2709103	Taquarana
__BRA__	27	AL	2709152	Teotônio Vilela
__BRA__	27	AL	2709202	Traipu
__BRA__	27	AL	2709301	União dos Palmares
__BRA__	27	AL	2709400	Viçosa
__BRA__	17	TO	1700251	Abreulândia
__BRA__	17	TO	1700301	Aguiarnópolis
__BRA__	17	TO	1700350	Aliança do Tocantins
__BRA__	17	TO	1700400	Almas
__BRA__	17	TO	1700707	Alvorada
__BRA__	17	TO	1701002	Ananás
__BRA__	17	TO	1701051	Angico
__BRA__	17	TO	1701101	Aparecida do Rio Negro
__BRA__	17	TO	1701309	Aragominas
__BRA__	17	TO	1701903	Araguacema
__BRA__	17	TO	1702000	Araguaçu
__BRA__	17	TO	1702109	Araguaína
__BRA__	17	TO	1702158	Araguanã
__BRA__	17	TO	1702208	Araguatins
__BRA__	17	TO	1702307	Arapoema
__BRA__	17	TO	1702406	Arraias
__BRA__	17	TO	1702554	Augustinópolis
__BRA__	17	TO	1702703	Aurora do Tocantins
__BRA__	17	TO	1702901	Axixá do Tocantins
__BRA__	17	TO	1703008	Babaçulândia
__BRA__	17	TO	1703057	Bandeirantes do Tocantins
__BRA__	17	TO	1703073	Barra do Ouro
__BRA__	17	TO	1703107	Barrolândia
__BRA__	17	TO	1703206	Bernardo Sayão
__BRA__	17	TO	1703305	Bom Jesus do Tocantins
__BRA__	17	TO	1703602	Brasilândia do Tocantins
__BRA__	17	TO	1703701	Brejinho de Nazaré
__BRA__	17	TO	1703800	Buriti do Tocantins
__BRA__	17	TO	1703826	Cachoeirinha
__BRA__	17	TO	1703842	Campos Lindos
__BRA__	17	TO	1703867	Cariri do Tocantins
__BRA__	17	TO	1703883	Carmolândia
__BRA__	17	TO	1703891	Carrasco Bonito
__BRA__	17	TO	1703909	Caseara
__BRA__	17	TO	1704105	Centenário
__BRA__	17	TO	1705102	Chapada da Natividade
__BRA__	17	TO	1704600	Chapada de Areia
__BRA__	17	TO	1705508	Colinas do Tocantins
__BRA__	17	TO	1716703	Colméia
__BRA__	17	TO	1705557	Combinado
__BRA__	17	TO	1705607	Conceição do Tocantins
__BRA__	17	TO	1706001	Couto de Magalhães
__BRA__	17	TO	1706100	Cristalândia
__BRA__	17	TO	1706258	Crixás do Tocantins
__BRA__	17	TO	1706506	Darcinópolis
__BRA__	17	TO	1707009	Dianópolis
__BRA__	17	TO	1707108	Divinópolis do Tocantins
__BRA__	17	TO	1707207	Dois Irmãos do Tocantins
__BRA__	17	TO	1707306	Dueré
__BRA__	17	TO	1707405	Esperantina
__BRA__	17	TO	1707553	Fátima
__BRA__	17	TO	1707652	Figueirópolis
__BRA__	17	TO	1707702	Filadélfia
__BRA__	17	TO	1708205	Formoso do Araguaia
__BRA__	17	TO	1708254	Fortaleza do Tabocão
__BRA__	17	TO	1708304	Goianorte
__BRA__	17	TO	1709005	Goiatins
__BRA__	17	TO	1709302	Guaraí
__BRA__	17	TO	1709500	Gurupi
__BRA__	17	TO	1709807	Ipueiras
__BRA__	17	TO	1710508	Itacajá
__BRA__	17	TO	1710706	Itaguatins
__BRA__	17	TO	1710904	Itapiratins
__BRA__	17	TO	1711100	Itaporã do Tocantins
__BRA__	17	TO	1711506	Jaú do Tocantins
__BRA__	17	TO	1711803	Juarina
__BRA__	17	TO	1711902	Lagoa da Confusão
__BRA__	17	TO	1711951	Lagoa do Tocantins
__BRA__	17	TO	1712009	Lajeado
__BRA__	17	TO	1712157	Lavandeira
__BRA__	17	TO	1712405	Lizarda
__BRA__	17	TO	1712454	Luzinópolis
__BRA__	17	TO	1712504	Marianópolis do Tocantins
__BRA__	17	TO	1712702	Mateiros
__BRA__	17	TO	1712801	Maurilândia do Tocantins
__BRA__	17	TO	1713205	Miracema do Tocantins
__BRA__	17	TO	1713304	Miranorte
__BRA__	17	TO	1713601	Monte do Carmo
__BRA__	17	TO	1713700	Monte Santo do Tocantins
__BRA__	17	TO	1713957	Muricilândia
__BRA__	17	TO	1714203	Natividade
__BRA__	17	TO	1714302	Nazaré
__BRA__	17	TO	1714880	Nova Olinda
__BRA__	17	TO	1715002	Nova Rosalândia
__BRA__	17	TO	1715101	Novo Acordo
__BRA__	17	TO	1715150	Novo Alegre
__BRA__	17	TO	1715259	Novo Jardim
__BRA__	17	TO	1715507	Oliveira de Fátima
__BRA__	17	TO	1721000	Palmas
__BRA__	17	TO	1715705	Palmeirante
__BRA__	17	TO	1713809	Palmeiras do Tocantins
__BRA__	17	TO	1715754	Palmeirópolis
__BRA__	17	TO	1716109	Paraíso do Tocantins
__BRA__	17	TO	1716208	Paranã
__BRA__	17	TO	1716307	Pau D'Arco
__BRA__	17	TO	1716505	Pedro Afonso
__BRA__	17	TO	1716604	Peixe
__BRA__	17	TO	1716653	Pequizeiro
__BRA__	17	TO	1717008	Pindorama do Tocantins
__BRA__	17	TO	1717206	Piraquê
__BRA__	17	TO	1717503	Pium
__BRA__	17	TO	1717800	Ponte Alta do Bom Jesus
__BRA__	17	TO	1717909	Ponte Alta do Tocantins
__BRA__	17	TO	1718006	Porto Alegre do Tocantins
__BRA__	17	TO	1718204	Porto Nacional
__BRA__	17	TO	1718303	Praia Norte
__BRA__	17	TO	1718402	Presidente Kennedy
__BRA__	17	TO	1718451	Pugmil
__BRA__	17	TO	1718501	Recursolândia
__BRA__	17	TO	1718550	Riachinho
__BRA__	17	TO	1718659	Rio da Conceição
__BRA__	17	TO	1718709	Rio dos Bois
__BRA__	17	TO	1718758	Rio Sono
__BRA__	17	TO	1718808	Sampaio
__BRA__	17	TO	1718840	Sandolândia
__BRA__	17	TO	1718865	Santa Fé do Araguaia
__BRA__	17	TO	1718881	Santa Maria do Tocantins
__BRA__	17	TO	1718899	Santa Rita do Tocantins
__BRA__	17	TO	1718907	Santa Rosa do Tocantins
__BRA__	17	TO	1719004	Santa Tereza do Tocantins
__BRA__	17	TO	1720002	Santa Terezinha do Tocantins
__BRA__	17	TO	1720101	São Bento do Tocantins
__BRA__	17	TO	1720150	São Félix do Tocantins
__BRA__	17	TO	1720200	São Miguel do Tocantins
__BRA__	17	TO	1720259	São Salvador do Tocantins
__BRA__	17	TO	1720309	São Sebastião do Tocantins
__BRA__	17	TO	1720499	São Valério da Natividade
__BRA__	17	TO	1720655	Silvanópolis
__BRA__	17	TO	1720804	Sítio Novo do Tocantins
__BRA__	17	TO	1720853	Sucupira
__BRA__	17	TO	1720903	Taguatinga
__BRA__	17	TO	1720937	Taipas do Tocantins
__BRA__	17	TO	1720978	Talismã
__BRA__	17	TO	1721109	Tocantínia
__BRA__	17	TO	1721208	Tocantinópolis
__BRA__	17	TO	1721257	Tupirama
__BRA__	17	TO	1721307	Tupiratins
__BRA__	17	TO	1722081	Wanderlândia
__BRA__	17	TO	1722107	Xambioá
__BRA__	51	MT	5100102	Acorizal
__BRA__	51	MT	5100201	Água Boa
__BRA__	51	MT	5100250	Alta Floresta
__BRA__	51	MT	5100300	Alto Araguaia
__BRA__	51	MT	5100359	Alto Boa Vista
__BRA__	51	MT	5100409	Alto Garças
__BRA__	51	MT	5100508	Alto Paraguai
__BRA__	51	MT	5100607	Alto Taquari
__BRA__	51	MT	5100805	Apiacás
__BRA__	51	MT	5101001	Araguaiana
__BRA__	51	MT	5101209	Araguainha
__BRA__	51	MT	5101258	Araputanga
__BRA__	51	MT	5101308	Arenápolis
__BRA__	51	MT	5101407	Aripuanã
__BRA__	51	MT	5101605	Barão de Melgaço
__BRA__	51	MT	5101704	Barra do Bugres
__BRA__	51	MT	5101803	Barra do Garças
__BRA__	51	MT	5101852	Bom Jesus do Araguaia
__BRA__	51	MT	5101902	Brasnorte
__BRA__	51	MT	5102504	Cáceres
__BRA__	51	MT	5102603	Campinápolis
__BRA__	51	MT	5102637	Campo Novo do Parecis
__BRA__	51	MT	5102678	Campo Verde
__BRA__	51	MT	5102686	Campos de Júlio
__BRA__	51	MT	5102694	Canabrava do Norte
__BRA__	51	MT	5102702	Canarana
__BRA__	51	MT	5102793	Carlinda
__BRA__	51	MT	5102850	Castanheira
__BRA__	51	MT	5103007	Chapada dos Guimarães
__BRA__	51	MT	5103056	Cláudia
__BRA__	51	MT	5103106	Cocalinho
__BRA__	51	MT	5103205	Colíder
__BRA__	51	MT	5103254	Colniza
__BRA__	51	MT	5103304	Comodoro
__BRA__	51	MT	5103353	Confresa
__BRA__	51	MT	5103361	Conquista D'Oeste
__BRA__	51	MT	5103379	Cotriguaçu
__BRA__	51	MT	5103403	Cuiabá
__BRA__	51	MT	5103437	Curvelândia
__BRA__	51	MT	5103452	Denise
__BRA__	51	MT	5103502	Diamantino
__BRA__	51	MT	5103601	Dom Aquino
__BRA__	51	MT	5103700	Feliz Natal
__BRA__	51	MT	5103809	Figueirópolis D'Oeste
__BRA__	51	MT	5103858	Gaúcha do Norte
__BRA__	51	MT	5103908	General Carneiro
__BRA__	51	MT	5103957	Glória D'Oeste
__BRA__	51	MT	5104104	Guarantã do Norte
__BRA__	51	MT	5104203	Guiratinga
__BRA__	51	MT	5104500	Indiavaí
__BRA__	51	MT	5104526	Ipiranga do Norte
__BRA__	51	MT	5104542	Itanhangá
__BRA__	51	MT	5104559	Itaúba
__BRA__	51	MT	5104609	Itiquira
__BRA__	51	MT	5104807	Jaciara
__BRA__	51	MT	5104906	Jangada
__BRA__	51	MT	5105002	Jauru
__BRA__	51	MT	5105101	Juara
__BRA__	51	MT	5105150	Juína
__BRA__	51	MT	5105176	Juruena
__BRA__	51	MT	5105200	Juscimeira
__BRA__	51	MT	5105234	Lambari D'Oeste
__BRA__	51	MT	5105259	Lucas do Rio Verde
__BRA__	51	MT	5105309	Luciára
__BRA__	51	MT	5105580	Marcelândia
__BRA__	51	MT	5105606	Matupá
__BRA__	51	MT	5105622	Mirassol d'Oeste
__BRA__	51	MT	5105903	Nobres
__BRA__	51	MT	5106000	Nortelândia
__BRA__	51	MT	5106109	Nossa Senhora do Livramento
__BRA__	51	MT	5106158	Nova Bandeirantes
__BRA__	51	MT	5106208	Nova Brasilândia
__BRA__	51	MT	5106216	Nova Canaã do Norte
__BRA__	51	MT	5108808	Nova Guarita
__BRA__	51	MT	5106182	Nova Lacerda
__BRA__	51	MT	5108857	Nova Marilândia
__BRA__	51	MT	5108907	Nova Maringá
__BRA__	51	MT	5108956	Nova Monte Verde
__BRA__	51	MT	5106224	Nova Mutum
__BRA__	51	MT	5106174	Nova Nazaré
__BRA__	51	MT	5106232	Nova Olímpia
__BRA__	51	MT	5106190	Nova Santa Helena
__BRA__	51	MT	5106240	Nova Ubiratã
__BRA__	51	MT	5106257	Nova Xavantina
__BRA__	51	MT	5106273	Novo Horizonte do Norte
__BRA__	51	MT	5106265	Novo Mundo
__BRA__	51	MT	5106315	Novo Santo Antônio
__BRA__	51	MT	5106281	Novo São Joaquim
__BRA__	51	MT	5106299	Paranaíta
__BRA__	51	MT	5106307	Paranatinga
__BRA__	51	MT	5106372	Pedra Preta
__BRA__	51	MT	5106422	Peixoto de Azevedo
__BRA__	51	MT	5106455	Planalto da Serra
__BRA__	51	MT	5106505	Poconé
__BRA__	51	MT	5106653	Pontal do Araguaia
__BRA__	51	MT	5106703	Ponte Branca
__BRA__	51	MT	5106752	Pontes e Lacerda
__BRA__	51	MT	5106778	Porto Alegre do Norte
__BRA__	51	MT	5106802	Porto dos Gaúchos
__BRA__	51	MT	5106828	Porto Esperidião
__BRA__	51	MT	5106851	Porto Estrela
__BRA__	51	MT	5107008	Poxoréo
__BRA__	51	MT	5107040	Primavera do Leste
__BRA__	51	MT	5107065	Querência
__BRA__	51	MT	5107156	Reserva do Cabaçal
__BRA__	51	MT	5107180	Ribeirão Cascalheira
__BRA__	51	MT	5107198	Ribeirãozinho
__BRA__	51	MT	5107206	Rio Branco
__BRA__	51	MT	5107578	Rondolândia
__BRA__	51	MT	5107602	Rondonópolis
__BRA__	51	MT	5107701	Rosário Oeste
__BRA__	51	MT	5107750	Salto do Céu
__BRA__	51	MT	5107248	Santa Carmem
__BRA__	51	MT	5107743	Santa Cruz do Xingu
__BRA__	51	MT	5107768	Santa Rita do Trivelato
__BRA__	51	MT	5107776	Santa Terezinha
__BRA__	51	MT	5107263	Santo Afonso
__BRA__	51	MT	5107792	Santo Antônio do Leste
__BRA__	51	MT	5107800	Santo Antônio do Leverger
__BRA__	51	MT	5107859	São Félix do Araguaia
__BRA__	51	MT	5107297	São José do Povo
__BRA__	51	MT	5107305	São José do Rio Claro
__BRA__	51	MT	5107354	São José do Xingu
__BRA__	51	MT	5107107	São José dos Quatro Marcos
__BRA__	51	MT	5107404	São Pedro da Cipa
__BRA__	51	MT	5107875	Sapezal
__BRA__	51	MT	5107883	Serra Nova Dourada
__BRA__	51	MT	5107909	Sinop
__BRA__	51	MT	5107925	Sorriso
__BRA__	51	MT	5107941	Tabaporã
__BRA__	51	MT	5107958	Tangará da Serra
__BRA__	51	MT	5108006	Tapurah
__BRA__	51	MT	5108055	Terra Nova do Norte
__BRA__	51	MT	5108105	Tesouro
__BRA__	51	MT	5108204	Torixoréu
__BRA__	51	MT	5108303	União do Sul
__BRA__	51	MT	5108352	Vale de São Domingos
__BRA__	51	MT	5108402	Várzea Grande
__BRA__	51	MT	5108501	Vera
__BRA__	51	MT	5105507	Vila Bela da Santíssima Trindade
__BRA__	51	MT	5108600	Vila Rica
__BRA__	15	PA	1500107	Abaetetuba
__BRA__	15	PA	1500131	Abel Figueiredo
__BRA__	15	PA	1500206	Acará
__BRA__	15	PA	1500305	Afuá
__BRA__	15	PA	1500347	Água Azul do Norte
__BRA__	15	PA	1500404	Alenquer
__BRA__	15	PA	1500503	Almeirim
__BRA__	15	PA	1500602	Altamira
__BRA__	15	PA	1500701	Anajás
__BRA__	15	PA	1500800	Ananindeua
__BRA__	15	PA	1500859	Anapu
__BRA__	15	PA	1500909	Augusto Corrêa
__BRA__	15	PA	1500958	Aurora do Pará
__BRA__	15	PA	1501006	Aveiro
__BRA__	15	PA	1501105	Bagre
__BRA__	15	PA	1501204	Baião
__BRA__	15	PA	1501253	Bannach
__BRA__	15	PA	1501303	Barcarena
__BRA__	15	PA	1501402	Belém
__BRA__	15	PA	1501451	Belterra
__BRA__	15	PA	1501501	Benevides
__BRA__	15	PA	1501576	Bom Jesus do Tocantins
__BRA__	15	PA	1501600	Bonito
__BRA__	15	PA	1501709	Bragança
__BRA__	15	PA	1501725	Brasil Novo
__BRA__	15	PA	1501758	Brejo Grande do Araguaia
__BRA__	15	PA	1501782	Breu Branco
__BRA__	15	PA	1501808	Breves
__BRA__	15	PA	1501907	Bujaru
__BRA__	15	PA	1502004	Cachoeira do Arari
__BRA__	15	PA	1501956	Cachoeira do Piriá
__BRA__	15	PA	1502103	Cametá
__BRA__	15	PA	1502152	Canaã dos Carajás
__BRA__	15	PA	1502202	Capanema
__BRA__	15	PA	1502301	Capitão Poço
__BRA__	15	PA	1502400	Castanhal
__BRA__	15	PA	1502509	Chaves
__BRA__	15	PA	1502608	Colares
__BRA__	15	PA	1502707	Conceição do Araguaia
__BRA__	15	PA	1502756	Concórdia do Pará
__BRA__	15	PA	1502764	Cumaru do Norte
__BRA__	15	PA	1502772	Curionópolis
__BRA__	15	PA	1502806	Curralinho
__BRA__	15	PA	1502855	Curuá
__BRA__	15	PA	1502905	Curuçá
__BRA__	15	PA	1502939	Dom Eliseu
__BRA__	15	PA	1502954	Eldorado dos Carajás
__BRA__	15	PA	1503002	Faro
__BRA__	15	PA	1503044	Floresta do Araguaia
__BRA__	15	PA	1503077	Garrafão do Norte
__BRA__	15	PA	1503093	Goianésia do Pará
__BRA__	15	PA	1503101	Gurupá
__BRA__	15	PA	1503200	Igarapé-Açu
__BRA__	15	PA	1503309	Igarapé-Miri
__BRA__	15	PA	1503408	Inhangapi
__BRA__	15	PA	1503457	Ipixuna do Pará
__BRA__	15	PA	1503507	Irituia
__BRA__	15	PA	1503606	Itaituba
__BRA__	15	PA	1503705	Itupiranga
__BRA__	15	PA	1503754	Jacareacanga
__BRA__	15	PA	1503804	Jacundá
__BRA__	15	PA	1503903	Juruti
__BRA__	15	PA	1504000	Limoeiro do Ajuru
__BRA__	15	PA	1504059	Mãe do Rio
__BRA__	15	PA	1504109	Magalhães Barata
__BRA__	15	PA	1504208	Marabá
__BRA__	15	PA	1504307	Maracanã
__BRA__	15	PA	1504406	Marapanim
__BRA__	15	PA	1504422	Marituba
__BRA__	15	PA	1504455	Medicilândia
__BRA__	15	PA	1504505	Melgaço
__BRA__	15	PA	1504604	Mocajuba
__BRA__	15	PA	1504703	Moju
__BRA__	15	PA	1504802	Monte Alegre
__BRA__	15	PA	1504901	Muaná
__BRA__	15	PA	1504950	Nova Esperança do Piriá
__BRA__	15	PA	1504976	Nova Ipixuna
__BRA__	15	PA	1505007	Nova Timboteua
__BRA__	15	PA	1505031	Novo Progresso
__BRA__	15	PA	1505064	Novo Repartimento
__BRA__	15	PA	1505106	Óbidos
__BRA__	15	PA	1505205	Oeiras do Pará
__BRA__	15	PA	1505304	Oriximiná
__BRA__	15	PA	1505403	Ourém
__BRA__	15	PA	1505437	Ourilândia do Norte
__BRA__	15	PA	1505486	Pacajá
__BRA__	15	PA	1505494	Palestina do Pará
__BRA__	15	PA	1505502	Paragominas
__BRA__	15	PA	1505536	Parauapebas
__BRA__	15	PA	1505551	Pau D'Arco
__BRA__	15	PA	1505601	Peixe-Boi
__BRA__	15	PA	1505635	Piçarra
__BRA__	15	PA	1505650	Placas
__BRA__	15	PA	1505700	Ponta de Pedras
__BRA__	15	PA	1505809	Portel
__BRA__	15	PA	1505908	Porto de Moz
__BRA__	15	PA	1506005	Prainha
__BRA__	15	PA	1506104	Primavera
__BRA__	15	PA	1506112	Quatipuru
__BRA__	15	PA	1506138	Redenção
__BRA__	15	PA	1506161	Rio Maria
__BRA__	15	PA	1506187	Rondon do Pará
__BRA__	15	PA	1506195	Rurópolis
__BRA__	15	PA	1506203	Salinópolis
__BRA__	15	PA	1506302	Salvaterra
__BRA__	15	PA	1506351	Santa Bárbara do Pará
__BRA__	15	PA	1506401	Santa Cruz do Arari
__BRA__	15	PA	1506500	Santa Isabel do Pará
__BRA__	15	PA	1506559	Santa Luzia do Pará
__BRA__	15	PA	1506583	Santa Maria das Barreiras
__BRA__	15	PA	1506609	Santa Maria do Pará
__BRA__	15	PA	1506708	Santana do Araguaia
__BRA__	15	PA	1506807	Santarém
__BRA__	15	PA	1506906	Santarém Novo
__BRA__	15	PA	1507003	Santo Antônio do Tauá
__BRA__	15	PA	1507102	São Caetano de Odivelas
__BRA__	15	PA	1507151	São Domingos do Araguaia
__BRA__	15	PA	1507201	São Domingos do Capim
__BRA__	15	PA	1507300	São Félix do Xingu
__BRA__	15	PA	1507409	São Francisco do Pará
__BRA__	15	PA	1507458	São Geraldo do Araguaia
__BRA__	15	PA	1507466	São João da Ponta
__BRA__	15	PA	1507474	São João de Pirabas
__BRA__	15	PA	1507508	São João do Araguaia
__BRA__	15	PA	1507607	São Miguel do Guamá
__BRA__	15	PA	1507706	São Sebastião da Boa Vista
__BRA__	15	PA	1507755	Sapucaia
__BRA__	15	PA	1507805	Senador José Porfírio
__BRA__	15	PA	1507904	Soure
__BRA__	15	PA	1507953	Tailândia
__BRA__	15	PA	1507961	Terra Alta
__BRA__	15	PA	1507979	Terra Santa
__BRA__	15	PA	1508001	Tomé-Açu
__BRA__	15	PA	1508035	Tracuateua
__BRA__	15	PA	1508050	Trairão
__BRA__	15	PA	1508084	Tucumã
__BRA__	15	PA	1508100	Tucuruí
__BRA__	15	PA	1508126	Ulianópolis
__BRA__	15	PA	1508159	Uruará
__BRA__	15	PA	1508209	Vigia
__BRA__	15	PA	1508308	Viseu
__BRA__	15	PA	1508357	Vitória do Xingu
__BRA__	15	PA	1508407	Xinguara
__BRA__	24	RN	2400109	Acari
__BRA__	24	RN	2400208	Açu
__BRA__	24	RN	2400307	Afonso Bezerra
__BRA__	24	RN	2400406	Água Nova
__BRA__	24	RN	2400505	Alexandria
__BRA__	24	RN	2400604	Almino Afonso
__BRA__	24	RN	2400703	Alto do Rodrigues
__BRA__	24	RN	2400802	Angicos
__BRA__	24	RN	2400901	Antônio Martins
__BRA__	24	RN	2401008	Apodi
__BRA__	24	RN	2401107	Areia Branca
__BRA__	24	RN	2401206	Arês
__BRA__	24	RN	2401305	Augusto Severo
__BRA__	24	RN	2401404	Baía Formosa
__BRA__	24	RN	2401453	Baraúna
__BRA__	24	RN	2401503	Barcelona
__BRA__	24	RN	2401602	Bento Fernandes
__BRA__	24	RN	2401651	Bodó
__BRA__	24	RN	2401701	Bom Jesus
__BRA__	24	RN	2401800	Brejinho
__BRA__	24	RN	2401859	Caiçara do Norte
__BRA__	24	RN	2401909	Caiçara do Rio do Vento
__BRA__	24	RN	2402006	Caicó
__BRA__	24	RN	2402105	Campo Redondo
__BRA__	24	RN	2402204	Canguaretama
__BRA__	24	RN	2402303	Caraúbas
__BRA__	24	RN	2402402	Carnaúba dos Dantas
__BRA__	24	RN	2402501	Carnaubais
__BRA__	24	RN	2402600	Ceará-Mirim
__BRA__	24	RN	2402709	Cerro Corá
__BRA__	24	RN	2402808	Coronel Ezequiel
__BRA__	24	RN	2402907	Coronel João Pessoa
__BRA__	24	RN	2403004	Cruzeta
__BRA__	24	RN	2403103	Currais Novos
__BRA__	24	RN	2403202	Doutor Severiano
__BRA__	24	RN	2403301	Encanto
__BRA__	24	RN	2403400	Equador
__BRA__	24	RN	2403509	Espírito Santo
__BRA__	24	RN	2403608	Extremoz
__BRA__	24	RN	2403707	Felipe Guerra
__BRA__	24	RN	2403756	Fernando Pedroza
__BRA__	24	RN	2403806	Florânia
__BRA__	24	RN	2403905	Francisco Dantas
__BRA__	24	RN	2404002	Frutuoso Gomes
__BRA__	24	RN	2404101	Galinhos
__BRA__	24	RN	2404200	Goianinha
__BRA__	24	RN	2404309	Governador Dix-Sept Rosado
__BRA__	24	RN	2404408	Grossos
__BRA__	24	RN	2404507	Guamaré
__BRA__	24	RN	2404606	Ielmo Marinho
__BRA__	24	RN	2404705	Ipanguaçu
__BRA__	24	RN	2404804	Ipueira
__BRA__	24	RN	2404853	Itajá
__BRA__	24	RN	2404903	Itaú
__BRA__	24	RN	2405009	Jaçanã
__BRA__	24	RN	2405108	Jandaíra
__BRA__	24	RN	2405207	Janduís
__BRA__	24	RN	2405306	Januário Cicco
__BRA__	24	RN	2405405	Japi
__BRA__	24	RN	2405504	Jardim de Angicos
__BRA__	24	RN	2405603	Jardim de Piranhas
__BRA__	24	RN	2405702	Jardim do Seridó
__BRA__	24	RN	2405801	João Câmara
__BRA__	24	RN	2405900	João Dias
__BRA__	24	RN	2406007	José da Penha
__BRA__	24	RN	2406106	Jucurutu
__BRA__	24	RN	2406155	Jundiá
__BRA__	24	RN	2406205	Lagoa d'Anta
__BRA__	24	RN	2406304	Lagoa de Pedras
__BRA__	24	RN	2406403	Lagoa de Velhos
__BRA__	24	RN	2406502	Lagoa Nova
__BRA__	24	RN	2406601	Lagoa Salgada
__BRA__	24	RN	2406700	Lajes
__BRA__	24	RN	2406809	Lajes Pintadas
__BRA__	24	RN	2406908	Lucrécia
__BRA__	24	RN	2407005	Luís Gomes
__BRA__	24	RN	2407104	Macaíba
__BRA__	24	RN	2407203	Macau
__BRA__	24	RN	2407252	Major Sales
__BRA__	24	RN	2407302	Marcelino Vieira
__BRA__	24	RN	2407401	Martins
__BRA__	24	RN	2407500	Maxaranguape
__BRA__	24	RN	2407609	Messias Targino
__BRA__	24	RN	2407708	Montanhas
__BRA__	24	RN	2407807	Monte Alegre
__BRA__	24	RN	2407906	Monte das Gameleiras
__BRA__	24	RN	2408003	Mossoró
__BRA__	24	RN	2408102	Natal
__BRA__	24	RN	2408201	Nísia Floresta
__BRA__	24	RN	2408300	Nova Cruz
__BRA__	24	RN	2408409	Olho-d'Água do Borges
__BRA__	24	RN	2408508	Ouro Branco
__BRA__	24	RN	2408607	Paraná
__BRA__	24	RN	2408706	Paraú
__BRA__	24	RN	2408805	Parazinho
__BRA__	24	RN	2408904	Parelhas
__BRA__	24	RN	2403251	Parnamirim
__BRA__	24	RN	2409100	Passa e Fica
__BRA__	24	RN	2409209	Passagem
__BRA__	24	RN	2409308	Patu
__BRA__	24	RN	2409407	Pau dos Ferros
__BRA__	24	RN	2409506	Pedra Grande
__BRA__	24	RN	2409605	Pedra Preta
__BRA__	24	RN	2409704	Pedro Avelino
__BRA__	24	RN	2409803	Pedro Velho
__BRA__	24	RN	2409902	Pendências
__BRA__	24	RN	2410009	Pilões
__BRA__	24	RN	2410108	Poço Branco
__BRA__	24	RN	2410207	Portalegre
__BRA__	24	RN	2410256	Porto do Mangue
__BRA__	24	RN	2410306	Presidente Juscelino
__BRA__	24	RN	2410405	Pureza
__BRA__	24	RN	2410504	Rafael Fernandes
__BRA__	24	RN	2410603	Rafael Godeiro
__BRA__	24	RN	2410702	Riacho da Cruz
__BRA__	24	RN	2410801	Riacho de Santana
__BRA__	24	RN	2410900	Riachuelo
__BRA__	24	RN	2408953	Rio do Fogo
__BRA__	24	RN	2411007	Rodolfo Fernandes
__BRA__	24	RN	2411106	Ruy Barbosa
__BRA__	24	RN	2411205	Santa Cruz
__BRA__	24	RN	2409332	Santa Maria
__BRA__	24	RN	2411403	Santana do Matos
__BRA__	24	RN	2411429	Santana do Seridó
__BRA__	24	RN	2411502	Santo Antônio
__BRA__	24	RN	2411601	São Bento do Norte
__BRA__	24	RN	2411700	São Bento do Trairí
__BRA__	24	RN	2411809	São Fernando
__BRA__	24	RN	2411908	São Francisco do Oeste
__BRA__	24	RN	2412005	São Gonçalo do Amarante
__BRA__	24	RN	2412104	São João do Sabugi
__BRA__	24	RN	2412203	São José de Mipibu
__BRA__	24	RN	2412302	São José do Campestre
__BRA__	24	RN	2412401	São José do Seridó
__BRA__	24	RN	2412500	São Miguel
__BRA__	24	RN	2412559	São Miguel do Gostoso
__BRA__	24	RN	2412609	São Paulo do Potengi
__BRA__	24	RN	2412708	São Pedro
__BRA__	24	RN	2412807	São Rafael
__BRA__	24	RN	2412906	São Tomé
__BRA__	24	RN	2413003	São Vicente
__BRA__	24	RN	2413102	Senador Elói de Souza
__BRA__	24	RN	2413201	Senador Georgino Avelino
__BRA__	24	RN	2413300	Serra de São Bento
__BRA__	24	RN	2413359	Serra do Mel
__BRA__	24	RN	2413409	Serra Negra do Norte
__BRA__	24	RN	2413508	Serrinha
__BRA__	24	RN	2413557	Serrinha dos Pintos
__BRA__	24	RN	2413607	Severiano Melo
__BRA__	24	RN	2413706	Sítio Novo
__BRA__	24	RN	2413805	Taboleiro Grande
__BRA__	24	RN	2413904	Taipu
__BRA__	24	RN	2414001	Tangará
__BRA__	24	RN	2414100	Tenente Ananias
__BRA__	24	RN	2414159	Tenente Laurentino Cruz
__BRA__	24	RN	2411056	Tibau
__BRA__	24	RN	2414209	Tibau do Sul
__BRA__	24	RN	2414308	Timbaúba dos Batistas
__BRA__	24	RN	2414407	Touros
__BRA__	24	RN	2414456	Triunfo Potiguar
__BRA__	24	RN	2414506	Umarizal
__BRA__	24	RN	2414605	Upanema
__BRA__	24	RN	2414704	Várzea
__BRA__	24	RN	2414753	Venha-Ver
__BRA__	24	RN	2414803	Vera Cruz
__BRA__	24	RN	2414902	Viçosa
__BRA__	24	RN	2415008	Vila Flor
__BRA__	23	CE	2300101	Abaiara
__BRA__	23	CE	2300150	Acarape
__BRA__	23	CE	2300200	Acaraú
__BRA__	23	CE	2300309	Acopiara
__BRA__	23	CE	2300408	Aiuaba
__BRA__	23	CE	2300507	Alcântaras
__BRA__	23	CE	2300606	Altaneira
__BRA__	23	CE	2300705	Alto Santo
__BRA__	23	CE	2300754	Amontada
__BRA__	23	CE	2300804	Antonina do Norte
__BRA__	23	CE	2300903	Apuiarés
__BRA__	23	CE	2301000	Aquiraz
__BRA__	23	CE	2301109	Aracati
__BRA__	23	CE	2301208	Aracoiaba
__BRA__	23	CE	2301257	Ararendá
__BRA__	23	CE	2301307	Araripe
__BRA__	23	CE	2301406	Aratuba
__BRA__	23	CE	2301505	Arneiroz
__BRA__	23	CE	2301604	Assaré
__BRA__	23	CE	2301703	Aurora
__BRA__	23	CE	2301802	Baixio
__BRA__	23	CE	2301851	Banabuiú
__BRA__	23	CE	2301901	Barbalha
__BRA__	23	CE	2301950	Barreira
__BRA__	23	CE	2302008	Barro
__BRA__	23	CE	2302057	Barroquinha
__BRA__	23	CE	2302107	Baturité
__BRA__	23	CE	2302206	Beberibe
__BRA__	23	CE	2302305	Bela Cruz
__BRA__	23	CE	2302404	Boa Viagem
__BRA__	23	CE	2302503	Brejo Santo
__BRA__	23	CE	2302602	Camocim
__BRA__	23	CE	2302701	Campos Sales
__BRA__	23	CE	2302800	Canindé
__BRA__	23	CE	2302909	Capistrano
__BRA__	23	CE	2303006	Caridade
__BRA__	23	CE	2303105	Cariré
__BRA__	23	CE	2303204	Caririaçu
__BRA__	23	CE	2303303	Cariús
__BRA__	23	CE	2303402	Carnaubal
__BRA__	23	CE	2303501	Cascavel
__BRA__	23	CE	2303600	Catarina
__BRA__	23	CE	2303659	Catunda
__BRA__	23	CE	2303709	Caucaia
__BRA__	23	CE	2303808	Cedro
__BRA__	23	CE	2303907	Chaval
__BRA__	23	CE	2303931	Choró
__BRA__	23	CE	2303956	Chorozinho
__BRA__	23	CE	2304004	Coreaú
__BRA__	23	CE	2304103	Crateús
__BRA__	23	CE	2304202	Crato
__BRA__	23	CE	2304236	Croatá
__BRA__	23	CE	2304251	Cruz
__BRA__	23	CE	2304269	Deputado Irapuan Pinheiro
__BRA__	23	CE	2304277	Ererê
__BRA__	23	CE	2304285	Eusébio
__BRA__	23	CE	2304301	Farias Brito
__BRA__	23	CE	2304350	Forquilha
__BRA__	23	CE	2304400	Fortaleza
__BRA__	23	CE	2304459	Fortim
__BRA__	23	CE	2304509	Frecheirinha
__BRA__	23	CE	2304608	General Sampaio
__BRA__	23	CE	2304657	Graça
__BRA__	23	CE	2304707	Granja
__BRA__	23	CE	2304806	Granjeiro
__BRA__	23	CE	2304905	Groaíras
__BRA__	23	CE	2304954	Guaiúba
__BRA__	23	CE	2305001	Guaraciaba do Norte
__BRA__	23	CE	2305100	Guaramiranga
__BRA__	23	CE	2305209	Hidrolândia
__BRA__	23	CE	2305233	Horizonte
__BRA__	23	CE	2305266	Ibaretama
__BRA__	23	CE	2305308	Ibiapina
__BRA__	23	CE	2305332	Ibicuitinga
__BRA__	23	CE	2305357	Icapuí
__BRA__	23	CE	2305407	Icó
__BRA__	23	CE	2305506	Iguatu
__BRA__	23	CE	2305605	Independência
__BRA__	23	CE	2305654	Ipaporanga
__BRA__	23	CE	2305704	Ipaumirim
__BRA__	23	CE	2305803	Ipu
__BRA__	23	CE	2305902	Ipueiras
__BRA__	23	CE	2306009	Iracema
__BRA__	23	CE	2306108	Irauçuba
__BRA__	23	CE	2306207	Itaiçaba
__BRA__	23	CE	2306256	Itaitinga
__BRA__	23	CE	2306306	Itapagé
__BRA__	23	CE	2306405	Itapipoca
__BRA__	23	CE	2306504	Itapiúna
__BRA__	23	CE	2306553	Itarema
__BRA__	23	CE	2306603	Itatira
__BRA__	23	CE	2306702	Jaguaretama
__BRA__	23	CE	2306801	Jaguaribara
__BRA__	23	CE	2306900	Jaguaribe
__BRA__	23	CE	2307007	Jaguaruana
__BRA__	23	CE	2307106	Jardim
__BRA__	23	CE	2307205	Jati
__BRA__	23	CE	2307254	Jijoca de Jericoacoara
__BRA__	23	CE	2307304	Juazeiro do Norte
__BRA__	23	CE	2307403	Jucás
__BRA__	23	CE	2307502	Lavras da Mangabeira
__BRA__	23	CE	2307601	Limoeiro do Norte
__BRA__	23	CE	2307635	Madalena
__BRA__	23	CE	2307650	Maracanaú
__BRA__	23	CE	2307700	Maranguape
__BRA__	23	CE	2307809	Marco
__BRA__	23	CE	2307908	Martinópole
__BRA__	23	CE	2308005	Massapê
__BRA__	23	CE	2308104	Mauriti
__BRA__	23	CE	2308203	Meruoca
__BRA__	23	CE	2308302	Milagres
__BRA__	23	CE	2308351	Milhã
__BRA__	23	CE	2308377	Miraíma
__BRA__	23	CE	2308401	Missão Velha
__BRA__	23	CE	2308500	Mombaça
__BRA__	23	CE	2308609	Monsenhor Tabosa
__BRA__	23	CE	2308708	Morada Nova
__BRA__	23	CE	2308807	Moraújo
__BRA__	23	CE	2308906	Morrinhos
__BRA__	23	CE	2309003	Mucambo
__BRA__	23	CE	2309102	Mulungu
__BRA__	23	CE	2309201	Nova Olinda
__BRA__	23	CE	2309300	Nova Russas
__BRA__	23	CE	2309409	Novo Oriente
__BRA__	23	CE	2309458	Ocara
__BRA__	23	CE	2309508	Orós
__BRA__	23	CE	2309607	Pacajus
__BRA__	23	CE	2309706	Pacatuba
__BRA__	23	CE	2309805	Pacoti
__BRA__	23	CE	2309904	Pacujá
__BRA__	23	CE	2310001	Palhano
__BRA__	23	CE	2310100	Palmácia
__BRA__	23	CE	2310209	Paracuru
__BRA__	23	CE	2310258	Paraipaba
__BRA__	23	CE	2310308	Parambu
__BRA__	23	CE	2310407	Paramoti
__BRA__	23	CE	2310506	Pedra Branca
__BRA__	23	CE	2310605	Penaforte
__BRA__	23	CE	2310704	Pentecoste
__BRA__	23	CE	2310803	Pereiro
__BRA__	23	CE	2310852	Pindoretama
__BRA__	23	CE	2310902	Piquet Carneiro
__BRA__	23	CE	2310951	Pires Ferreira
__BRA__	23	CE	2311009	Poranga
__BRA__	23	CE	2311108	Porteiras
__BRA__	23	CE	2311207	Potengi
__BRA__	23	CE	2311231	Potiretama
__BRA__	23	CE	2311264	Quiterianópolis
__BRA__	23	CE	2311306	Quixadá
__BRA__	23	CE	2311355	Quixelô
__BRA__	23	CE	2311405	Quixeramobim
__BRA__	23	CE	2311504	Quixeré
__BRA__	23	CE	2311603	Redenção
__BRA__	23	CE	2311702	Reriutaba
__BRA__	23	CE	2311801	Russas
__BRA__	23	CE	2311900	Saboeiro
__BRA__	23	CE	2311959	Salitre
__BRA__	23	CE	2312205	Santa Quitéria
__BRA__	23	CE	2312007	Santana do Acaraú
__BRA__	23	CE	2312106	Santana do Cariri
__BRA__	23	CE	2312304	São Benedito
__BRA__	23	CE	2312403	São Gonçalo do Amarante
__BRA__	23	CE	2312502	São João do Jaguaribe
__BRA__	23	CE	2312601	São Luís do Curu
__BRA__	23	CE	2312700	Senador Pompeu
__BRA__	23	CE	2312809	Senador Sá
__BRA__	23	CE	2312908	Sobral
__BRA__	23	CE	2313005	Solonópole
__BRA__	23	CE	2313104	Tabuleiro do Norte
__BRA__	23	CE	2313203	Tamboril
__BRA__	23	CE	2313252	Tarrafas
__BRA__	23	CE	2313302	Tauá
__BRA__	23	CE	2313351	Tejuçuoca
__BRA__	23	CE	2313401	Tianguá
__BRA__	23	CE	2313500	Trairi
__BRA__	23	CE	2313559	Tururu
__BRA__	23	CE	2313609	Ubajara
__BRA__	23	CE	2313708	Umari
__BRA__	23	CE	2313757	Umirim
__BRA__	23	CE	2313807	Uruburetama
__BRA__	23	CE	2313906	Uruoca
__BRA__	23	CE	2313955	Varjota
__BRA__	23	CE	2314003	Várzea Alegre
__BRA__	23	CE	2314102	Viçosa do Ceará
__BRA__	26	PE	2600054	Abreu e Lima
__BRA__	26	PE	2600104	Afogados da Ingazeira
__BRA__	26	PE	2600203	Afrânio
__BRA__	26	PE	2600302	Agrestina
__BRA__	26	PE	2600401	Água Preta
__BRA__	26	PE	2600500	Águas Belas
__BRA__	26	PE	2600609	Alagoinha
__BRA__	26	PE	2600708	Aliança
__BRA__	26	PE	2600807	Altinho
__BRA__	26	PE	2600906	Amaraji
__BRA__	26	PE	2601003	Angelim
__BRA__	26	PE	2601052	Araçoiaba
__BRA__	26	PE	2601102	Araripina
__BRA__	26	PE	2601201	Arcoverde
__BRA__	26	PE	2601300	Barra de Guabiraba
__BRA__	26	PE	2601409	Barreiros
__BRA__	26	PE	2601508	Belém de Maria
__BRA__	26	PE	2601607	Belém de São Francisco
__BRA__	26	PE	2601706	Belo Jardim
__BRA__	26	PE	2601805	Betânia
__BRA__	26	PE	2601904	Bezerros
__BRA__	26	PE	2602001	Bodocó
__BRA__	26	PE	2602100	Bom Conselho
__BRA__	26	PE	2602209	Bom Jardim
__BRA__	26	PE	2602308	Bonito
__BRA__	26	PE	2602407	Brejão
__BRA__	26	PE	2602506	Brejinho
__BRA__	26	PE	2602605	Brejo da Madre de Deus
__BRA__	26	PE	2602704	Buenos Aires
__BRA__	26	PE	2602803	Buíque
__BRA__	26	PE	2602902	Cabo de Santo Agostinho
__BRA__	26	PE	2603009	Cabrobó
__BRA__	26	PE	2603108	Cachoeirinha
__BRA__	26	PE	2603207	Caetés
__BRA__	26	PE	2603306	Calçado
__BRA__	26	PE	2603405	Calumbi
__BRA__	26	PE	2603454	Camaragibe
__BRA__	26	PE	2603504	Camocim de São Félix
__BRA__	26	PE	2603603	Camutanga
__BRA__	26	PE	2603702	Canhotinho
__BRA__	26	PE	2603801	Capoeiras
__BRA__	26	PE	2603900	Carnaíba
__BRA__	26	PE	2603926	Carnaubeira da Penha
__BRA__	26	PE	2604007	Carpina
__BRA__	26	PE	2604106	Caruaru
__BRA__	26	PE	2604155	Casinhas
__BRA__	26	PE	2604205	Catende
__BRA__	26	PE	2604304	Cedro
__BRA__	26	PE	2604403	Chã de Alegria
__BRA__	26	PE	2604502	Chã Grande
__BRA__	26	PE	2604601	Condado
__BRA__	26	PE	2604700	Correntes
__BRA__	26	PE	2604809	Cortês
__BRA__	26	PE	2604908	Cumaru
__BRA__	26	PE	2605004	Cupira
__BRA__	26	PE	2605103	Custódia
__BRA__	26	PE	2605152	Dormentes
__BRA__	26	PE	2605202	Escada
__BRA__	26	PE	2605301	Exu
__BRA__	26	PE	2605400	Feira Nova
__BRA__	26	PE	2605459	Fernando de Noronha
__BRA__	26	PE	2605509	Ferreiros
__BRA__	26	PE	2605608	Flores
__BRA__	26	PE	2605707	Floresta
__BRA__	26	PE	2605806	Frei Miguelinho
__BRA__	26	PE	2605905	Gameleira
__BRA__	26	PE	2606002	Garanhuns
__BRA__	26	PE	2606101	Glória do Goitá
__BRA__	26	PE	2606200	Goiana
__BRA__	26	PE	2606309	Granito
__BRA__	26	PE	2606408	Gravatá
__BRA__	26	PE	2606507	Iati
__BRA__	26	PE	2606606	Ibimirim
__BRA__	26	PE	2606705	Ibirajuba
__BRA__	26	PE	2606804	Igarassu
__BRA__	26	PE	2606903	Iguaraci
__BRA__	26	PE	2607604	Ilha de Itamaracá
__BRA__	26	PE	2607000	Inajá
__BRA__	26	PE	2607109	Ingazeira
__BRA__	26	PE	2607208	Ipojuca
__BRA__	26	PE	2607307	Ipubi
__BRA__	26	PE	2607406	Itacuruba
__BRA__	26	PE	2607505	Itaíba
__BRA__	26	PE	2607653	Itambé
__BRA__	26	PE	2607703	Itapetim
__BRA__	26	PE	2607752	Itapissuma
__BRA__	26	PE	2607802	Itaquitinga
__BRA__	26	PE	2607901	Jaboatão dos Guararapes
__BRA__	26	PE	2607950	Jaqueira
__BRA__	26	PE	2608008	Jataúba
__BRA__	26	PE	2608057	Jatobá
__BRA__	26	PE	2608107	João Alfredo
__BRA__	26	PE	2608206	Joaquim Nabuco
__BRA__	26	PE	2608255	Jucati
__BRA__	26	PE	2608305	Jupi
__BRA__	26	PE	2608404	Jurema
__BRA__	26	PE	2608453	Lagoa do Carro
__BRA__	26	PE	2608503	Lagoa do Itaenga
__BRA__	26	PE	2608602	Lagoa do Ouro
__BRA__	26	PE	2608701	Lagoa dos Gatos
__BRA__	26	PE	2608750	Lagoa Grande
__BRA__	26	PE	2608800	Lajedo
__BRA__	26	PE	2608909	Limoeiro
__BRA__	26	PE	2609006	Macaparana
__BRA__	26	PE	2609105	Machados
__BRA__	26	PE	2609154	Manari
__BRA__	26	PE	2609204	Maraial
__BRA__	26	PE	2609303	Mirandiba
__BRA__	26	PE	2614303	Moreilândia
__BRA__	26	PE	2609402	Moreno
__BRA__	26	PE	2609501	Nazaré da Mata
__BRA__	26	PE	2609600	Olinda
__BRA__	26	PE	2609709	Orobó
__BRA__	26	PE	2609808	Orocó
__BRA__	26	PE	2609907	Ouricuri
__BRA__	26	PE	2610004	Palmares
__BRA__	26	PE	2610103	Palmeirina
__BRA__	26	PE	2610202	Panelas
__BRA__	26	PE	2610301	Paranatama
__BRA__	26	PE	2610400	Parnamirim
__BRA__	26	PE	2610509	Passira
__BRA__	26	PE	2610608	Paudalho
__BRA__	26	PE	2610707	Paulista
__BRA__	26	PE	2610806	Pedra
__BRA__	26	PE	2610905	Pesqueira
__BRA__	26	PE	2611002	Petrolândia
__BRA__	26	PE	2611101	Petrolina
__BRA__	26	PE	2611200	Poção
__BRA__	26	PE	2611309	Pombos
__BRA__	26	PE	2611408	Primavera
__BRA__	26	PE	2611507	Quipapá
__BRA__	26	PE	2611533	Quixaba
__BRA__	26	PE	2611606	Recife
__BRA__	26	PE	2611705	Riacho das Almas
__BRA__	26	PE	2611804	Ribeirão
__BRA__	26	PE	2611903	Rio Formoso
__BRA__	26	PE	2612000	Sairé
__BRA__	26	PE	2612109	Salgadinho
__BRA__	26	PE	2612208	Salgueiro
__BRA__	26	PE	2612307	Saloá
__BRA__	26	PE	2612406	Sanharó
__BRA__	26	PE	2612455	Santa Cruz
__BRA__	26	PE	2612471	Santa Cruz da Baixa Verde
__BRA__	26	PE	2612505	Santa Cruz do Capibaribe
__BRA__	26	PE	2612554	Santa Filomena
__BRA__	26	PE	2612604	Santa Maria da Boa Vista
__BRA__	26	PE	2612703	Santa Maria do Cambucá
__BRA__	26	PE	2612802	Santa Terezinha
__BRA__	26	PE	2612901	São Benedito do Sul
__BRA__	26	PE	2613008	São Bento do Una
__BRA__	26	PE	2613107	São Caitano
__BRA__	26	PE	2613206	São João
__BRA__	26	PE	2613305	São Joaquim do Monte
__BRA__	26	PE	2613404	São José da Coroa Grande
__BRA__	26	PE	2613503	São José do Belmonte
__BRA__	26	PE	2613602	São José do Egito
__BRA__	26	PE	2613701	São Lourenço da Mata
__BRA__	26	PE	2613800	São Vicente Ferrer
__BRA__	26	PE	2613909	Serra Talhada
__BRA__	26	PE	2614006	Serrita
__BRA__	26	PE	2614105	Sertânia
__BRA__	26	PE	2614204	Sirinhaém
__BRA__	26	PE	2614402	Solidão
__BRA__	26	PE	2614501	Surubim
__BRA__	26	PE	2614600	Tabira
__BRA__	26	PE	2614709	Tacaimbó
__BRA__	26	PE	2614808	Tacaratu
__BRA__	26	PE	2614857	Tamandaré
__BRA__	26	PE	2615003	Taquaritinga do Norte
__BRA__	26	PE	2615102	Terezinha
__BRA__	26	PE	2615201	Terra Nova
__BRA__	26	PE	2615300	Timbaúba
__BRA__	26	PE	2615409	Toritama
__BRA__	26	PE	2615508	Tracunhaém
__BRA__	26	PE	2615607	Trindade
__BRA__	26	PE	2615706	Triunfo
__BRA__	26	PE	2615805	Tupanatinga
__BRA__	26	PE	2615904	Tuparetama
__BRA__	26	PE	2616001	Venturosa
__BRA__	26	PE	2616100	Verdejante
__BRA__	26	PE	2616183	Vertente do Lério
__BRA__	26	PE	2616209	Vertentes
__BRA__	26	PE	2616308	Vicência
__BRA__	26	PE	2616407	Vitória de Santo Antão
__BRA__	26	PE	2616506	Xexéu
__BRA__	21	MA	2100055	Açailândia
__BRA__	21	MA	2100105	Afonso Cunha
__BRA__	21	MA	2100154	Água Doce do Maranhão
__BRA__	21	MA	2100204	Alcântara
__BRA__	21	MA	2100303	Aldeias Altas
__BRA__	21	MA	2100402	Altamira do Maranhão
__BRA__	21	MA	2100436	Alto Alegre do Maranhão
__BRA__	21	MA	2100477	Alto Alegre do Pindaré
__BRA__	21	MA	2100501	Alto Parnaíba
__BRA__	21	MA	2100550	Amapá do Maranhão
__BRA__	21	MA	2100600	Amarante do Maranhão
__BRA__	21	MA	2100709	Anajatuba
__BRA__	21	MA	2100808	Anapurus
__BRA__	21	MA	2100832	Apicum-Açu
__BRA__	21	MA	2100873	Araguanã
__BRA__	21	MA	2100907	Araioses
__BRA__	21	MA	2100956	Arame
__BRA__	21	MA	2101004	Arari
__BRA__	21	MA	2101103	Axixá
__BRA__	21	MA	2101202	Bacabal
__BRA__	21	MA	2101251	Bacabeira
__BRA__	21	MA	2101301	Bacuri
__BRA__	21	MA	2101350	Bacurituba
__BRA__	21	MA	2101400	Balsas
__BRA__	21	MA	2101509	Barão de Grajaú
__BRA__	21	MA	2101608	Barra do Corda
__BRA__	21	MA	2101707	Barreirinhas
__BRA__	21	MA	2101772	Bela Vista do Maranhão
__BRA__	21	MA	2101731	Belágua
__BRA__	21	MA	2101806	Benedito Leite
__BRA__	21	MA	2101905	Bequimão
__BRA__	21	MA	2101939	Bernardo do Mearim
__BRA__	21	MA	2101970	Boa Vista do Gurupi
__BRA__	21	MA	2102002	Bom Jardim
__BRA__	21	MA	2102036	Bom Jesus das Selvas
__BRA__	21	MA	2102077	Bom Lugar
__BRA__	21	MA	2102101	Brejo
__BRA__	21	MA	2102150	Brejo de Areia
__BRA__	21	MA	2102200	Buriti
__BRA__	21	MA	2102309	Buriti Bravo
__BRA__	21	MA	2102325	Buriticupu
__BRA__	21	MA	2102358	Buritirana
__BRA__	21	MA	2102374	Cachoeira Grande
__BRA__	21	MA	2102408	Cajapió
__BRA__	21	MA	2102507	Cajari
__BRA__	21	MA	2102556	Campestre do Maranhão
__BRA__	21	MA	2102606	Cândido Mendes
__BRA__	21	MA	2102705	Cantanhede
__BRA__	21	MA	2102754	Capinzal do Norte
__BRA__	21	MA	2102804	Carolina
__BRA__	21	MA	2102903	Carutapera
__BRA__	21	MA	2103000	Caxias
__BRA__	21	MA	2103109	Cedral
__BRA__	21	MA	2103125	Central do Maranhão
__BRA__	21	MA	2103158	Centro do Guilherme
__BRA__	21	MA	2103174	Centro Novo do Maranhão
__BRA__	21	MA	2103208	Chapadinha
__BRA__	21	MA	2103257	Cidelândia
__BRA__	21	MA	2103307	Codó
__BRA__	21	MA	2103406	Coelho Neto
__BRA__	21	MA	2103505	Colinas
__BRA__	21	MA	2103554	Conceição do Lago-Açu
__BRA__	21	MA	2103604	Coroatá
__BRA__	21	MA	2103703	Cururupu
__BRA__	21	MA	2103752	Davinópolis
__BRA__	21	MA	2103802	Dom Pedro
__BRA__	21	MA	2103901	Duque Bacelar
__BRA__	21	MA	2104008	Esperantinópolis
__BRA__	21	MA	2104057	Estreito
__BRA__	21	MA	2104073	Feira Nova do Maranhão
__BRA__	21	MA	2104081	Fernando Falcão
__BRA__	21	MA	2104099	Formosa da Serra Negra
__BRA__	21	MA	2104107	Fortaleza dos Nogueiras
__BRA__	21	MA	2104206	Fortuna
__BRA__	21	MA	2104305	Godofredo Viana
__BRA__	21	MA	2104404	Gonçalves Dias
__BRA__	21	MA	2104503	Governador Archer
__BRA__	21	MA	2104552	Governador Edison Lobão
__BRA__	21	MA	2104602	Governador Eugênio Barros
__BRA__	21	MA	2104628	Governador Luiz Rocha
__BRA__	21	MA	2104651	Governador Newton Bello
__BRA__	21	MA	2104677	Governador Nunes Freire
__BRA__	21	MA	2104701	Graça Aranha
__BRA__	21	MA	2104800	Grajaú
__BRA__	21	MA	2104909	Guimarães
__BRA__	21	MA	2105005	Humberto de Campos
__BRA__	21	MA	2105104	Icatu
__BRA__	21	MA	2105153	Igarapé do Meio
__BRA__	21	MA	2105203	Igarapé Grande
__BRA__	21	MA	2105302	Imperatriz
__BRA__	21	MA	2105351	Itaipava do Grajaú
__BRA__	21	MA	2105401	Itapecuru Mirim
__BRA__	21	MA	2105427	Itinga do Maranhão
__BRA__	21	MA	2105450	Jatobá
__BRA__	21	MA	2105476	Jenipapo dos Vieiras
__BRA__	21	MA	2105500	João Lisboa
__BRA__	21	MA	2105609	Joselândia
__BRA__	21	MA	2105658	Junco do Maranhão
__BRA__	21	MA	2105708	Lago da Pedra
__BRA__	21	MA	2105807	Lago do Junco
__BRA__	21	MA	2105948	Lago dos Rodrigues
__BRA__	21	MA	2105906	Lago Verde
__BRA__	21	MA	2105922	Lagoa do Mato
__BRA__	21	MA	2105963	Lagoa Grande do Maranhão
__BRA__	21	MA	2105989	Lajeado Novo
__BRA__	21	MA	2106003	Lima Campos
__BRA__	21	MA	2106102	Loreto
__BRA__	21	MA	2106201	Luís Domingues
__BRA__	21	MA	2106300	Magalhães de Almeida
__BRA__	21	MA	2106326	Maracaçumé
__BRA__	21	MA	2106359	Marajá do Sena
__BRA__	21	MA	2106375	Maranhãozinho
__BRA__	21	MA	2106409	Mata Roma
__BRA__	21	MA	2106508	Matinha
__BRA__	21	MA	2106607	Matões
__BRA__	21	MA	2106631	Matões do Norte
__BRA__	21	MA	2106672	Milagres do Maranhão
__BRA__	21	MA	2106706	Mirador
__BRA__	21	MA	2106755	Miranda do Norte
__BRA__	21	MA	2106805	Mirinzal
__BRA__	21	MA	2106904	Monção
__BRA__	21	MA	2107001	Montes Altos
__BRA__	21	MA	2107100	Morros
__BRA__	21	MA	2107209	Nina Rodrigues
__BRA__	21	MA	2107258	Nova Colinas
__BRA__	21	MA	2107308	Nova Iorque
__BRA__	21	MA	2107357	Nova Olinda do Maranhão
__BRA__	21	MA	2107407	Olho d'Água das Cunhãs
__BRA__	21	MA	2107456	Olinda Nova do Maranhão
__BRA__	21	MA	2107506	Paço do Lumiar
__BRA__	21	MA	2107605	Palmeirândia
__BRA__	21	MA	2107704	Paraibano
__BRA__	21	MA	2107803	Parnarama
__BRA__	21	MA	2107902	Passagem Franca
__BRA__	21	MA	2108009	Pastos Bons
__BRA__	21	MA	2108058	Paulino Neves
__BRA__	21	MA	2108108	Paulo Ramos
__BRA__	21	MA	2108207	Pedreiras
__BRA__	21	MA	2108256	Pedro do Rosário
__BRA__	21	MA	2108306	Penalva
__BRA__	21	MA	2108405	Peri Mirim
__BRA__	21	MA	2108454	Peritoró
__BRA__	21	MA	2108504	Pindaré-Mirim
__BRA__	21	MA	2108603	Pinheiro
__BRA__	21	MA	2108702	Pio XII
__BRA__	21	MA	2108801	Pirapemas
__BRA__	21	MA	2108900	Poção de Pedras
__BRA__	21	MA	2109007	Porto Franco
__BRA__	21	MA	2109056	Porto Rico do Maranhão
__BRA__	21	MA	2109106	Presidente Dutra
__BRA__	21	MA	2109205	Presidente Juscelino
__BRA__	21	MA	2109239	Presidente Médici
__BRA__	21	MA	2109270	Presidente Sarney
__BRA__	21	MA	2109304	Presidente Vargas
__BRA__	21	MA	2109403	Primeira Cruz
__BRA__	21	MA	2109452	Raposa
__BRA__	21	MA	2109502	Riachão
__BRA__	21	MA	2109551	Ribamar Fiquene
__BRA__	21	MA	2109601	Rosário
__BRA__	21	MA	2109700	Sambaíba
__BRA__	21	MA	2109759	Santa Filomena do Maranhão
__BRA__	21	MA	2109809	Santa Helena
__BRA__	21	MA	2109908	Santa Inês
__BRA__	21	MA	2110005	Santa Luzia
__BRA__	21	MA	2110039	Santa Luzia do Paruá
__BRA__	21	MA	2110104	Santa Quitéria do Maranhão
__BRA__	21	MA	2110203	Santa Rita
__BRA__	21	MA	2110237	Santana do Maranhão
__BRA__	21	MA	2110278	Santo Amaro do Maranhão
__BRA__	21	MA	2110302	Santo Antônio dos Lopes
__BRA__	21	MA	2110401	São Benedito do Rio Preto
__BRA__	21	MA	2110500	São Bento
__BRA__	21	MA	2110609	São Bernardo
__BRA__	21	MA	2110658	São Domingos do Azeitão
__BRA__	21	MA	2110708	São Domingos do Maranhão
__BRA__	21	MA	2110807	São Félix de Balsas
__BRA__	21	MA	2110856	São Francisco do Brejão
__BRA__	21	MA	2110906	São Francisco do Maranhão
__BRA__	21	MA	2111003	São João Batista
__BRA__	21	MA	2111029	São João do Carú
__BRA__	21	MA	2111052	São João do Paraíso
__BRA__	21	MA	2111078	São João do Soter
__BRA__	21	MA	2111102	São João dos Patos
__BRA__	21	MA	2111201	São José de Ribamar
__BRA__	21	MA	2111250	São José dos Basílios
__BRA__	21	MA	2111300	São Luís
__BRA__	21	MA	2111409	São Luís Gonzaga do Maranhão
__BRA__	21	MA	2111508	São Mateus do Maranhão
__BRA__	21	MA	2111532	São Pedro da Água Branca
__BRA__	21	MA	2111573	São Pedro dos Crentes
__BRA__	21	MA	2111607	São Raimundo das Mangabeiras
__BRA__	21	MA	2111631	São Raimundo do Doca Bezerra
__BRA__	21	MA	2111672	São Roberto
__BRA__	21	MA	2111706	São Vicente Ferrer
__BRA__	21	MA	2111722	Satubinha
__BRA__	21	MA	2111748	Senador Alexandre Costa
__BRA__	21	MA	2111763	Senador La Rocque
__BRA__	21	MA	2111789	Serrano do Maranhão
__BRA__	21	MA	2111805	Sítio Novo
__BRA__	21	MA	2111904	Sucupira do Norte
__BRA__	21	MA	2111953	Sucupira do Riachão
__BRA__	21	MA	2112001	Tasso Fragoso
__BRA__	21	MA	2112100	Timbiras
__BRA__	21	MA	2112209	Timon
__BRA__	21	MA	2112233	Trizidela do Vale
__BRA__	21	MA	2112274	Tufilândia
__BRA__	21	MA	2112308	Tuntum
__BRA__	21	MA	2112407	Turiaçu
__BRA__	21	MA	2112456	Turilândia
__BRA__	21	MA	2112506	Tutóia
__BRA__	21	MA	2112605	Urbano Santos
__BRA__	21	MA	2112704	Vargem Grande
__BRA__	21	MA	2112803	Viana
__BRA__	21	MA	2112852	Vila Nova dos Martírios
__BRA__	21	MA	2112902	Vitória do Mearim
__BRA__	21	MA	2113009	Vitorino Freire
__BRA__	21	MA	2114007	Zé Doca
__BRA__	22	PI	2200053	Acauã
__BRA__	22	PI	2200103	Agricolândia
__BRA__	22	PI	2200202	Água Branca
__BRA__	22	PI	2200251	Alagoinha do Piauí
__BRA__	22	PI	2200277	Alegrete do Piauí
__BRA__	22	PI	2200301	Alto Longá
__BRA__	22	PI	2200400	Altos
__BRA__	22	PI	2200459	Alvorada do Gurguéia
__BRA__	22	PI	2200509	Amarante
__BRA__	22	PI	2200608	Angical do Piauí
__BRA__	22	PI	2200707	Anísio de Abreu
__BRA__	22	PI	2200806	Antônio Almeida
__BRA__	22	PI	2200905	Aroazes
__BRA__	22	PI	2200954	Aroeiras do Itaim
__BRA__	22	PI	2201002	Arraial
__BRA__	22	PI	2201051	Assunção do Piauí
__BRA__	22	PI	2201101	Avelino Lopes
__BRA__	22	PI	2201150	Baixa Grande do Ribeiro
__BRA__	22	PI	2201176	Barra D'Alcântara
__BRA__	22	PI	2201200	Barras
__BRA__	22	PI	2201309	Barreiras do Piauí
__BRA__	22	PI	2201408	Barro Duro
__BRA__	22	PI	2201507	Batalha
__BRA__	22	PI	2201556	Bela Vista do Piauí
__BRA__	22	PI	2201572	Belém do Piauí
__BRA__	22	PI	2201606	Beneditinos
__BRA__	22	PI	2201705	Bertolínia
__BRA__	22	PI	2201739	Betânia do Piauí
__BRA__	22	PI	2201770	Boa Hora
__BRA__	22	PI	2201804	Bocaina
__BRA__	22	PI	2201903	Bom Jesus
__BRA__	22	PI	2201919	Bom Princípio do Piauí
__BRA__	22	PI	2201929	Bonfim do Piauí
__BRA__	22	PI	2201945	Boqueirão do Piauí
__BRA__	22	PI	2201960	Brasileira
__BRA__	22	PI	2201988	Brejo do Piauí
__BRA__	22	PI	2202000	Buriti dos Lopes
__BRA__	22	PI	2202026	Buriti dos Montes
__BRA__	22	PI	2202059	Cabeceiras do Piauí
__BRA__	22	PI	2202075	Cajazeiras do Piauí
__BRA__	22	PI	2202083	Cajueiro da Praia
__BRA__	22	PI	2202091	Caldeirão Grande do Piauí
__BRA__	22	PI	2202109	Campinas do Piauí
__BRA__	22	PI	2202117	Campo Alegre do Fidalgo
__BRA__	22	PI	2202133	Campo Grande do Piauí
__BRA__	22	PI	2202174	Campo Largo do Piauí
__BRA__	22	PI	2202208	Campo Maior
__BRA__	22	PI	2202251	Canavieira
__BRA__	22	PI	2202307	Canto do Buriti
__BRA__	22	PI	2202406	Capitão de Campos
__BRA__	22	PI	2202455	Capitão Gervásio Oliveira
__BRA__	22	PI	2202505	Caracol
__BRA__	22	PI	2202539	Caraúbas do Piauí
__BRA__	22	PI	2202554	Caridade do Piauí
__BRA__	22	PI	2202604	Castelo do Piauí
__BRA__	22	PI	2202653	Caxingó
__BRA__	22	PI	2202703	Cocal
__BRA__	22	PI	2202711	Cocal de Telha
__BRA__	22	PI	2202729	Cocal dos Alves
__BRA__	22	PI	2202737	Coivaras
__BRA__	22	PI	2202752	Colônia do Gurguéia
__BRA__	22	PI	2202778	Colônia do Piauí
__BRA__	22	PI	2202802	Conceição do Canindé
__BRA__	22	PI	2202851	Coronel José Dias
__BRA__	22	PI	2202901	Corrente
__BRA__	22	PI	2203008	Cristalândia do Piauí
__BRA__	22	PI	2203107	Cristino Castro
__BRA__	22	PI	2203206	Curimatá
__BRA__	22	PI	2203230	Currais
__BRA__	22	PI	2203271	Curral Novo do Piauí
__BRA__	22	PI	2203255	Curralinhos
__BRA__	22	PI	2203305	Demerval Lobão
__BRA__	22	PI	2203354	Dirceu Arcoverde
__BRA__	22	PI	2203404	Dom Expedito Lopes
__BRA__	22	PI	2203453	Dom Inocêncio
__BRA__	22	PI	2203420	Domingos Mourão
__BRA__	22	PI	2203503	Elesbão Veloso
__BRA__	22	PI	2203602	Eliseu Martins
__BRA__	22	PI	2203701	Esperantina
__BRA__	22	PI	2203750	Fartura do Piauí
__BRA__	22	PI	2203800	Flores do Piauí
__BRA__	22	PI	2203859	Floresta do Piauí
__BRA__	22	PI	2203909	Floriano
__BRA__	22	PI	2204006	Francinópolis
__BRA__	22	PI	2204105	Francisco Ayres
__BRA__	22	PI	2204154	Francisco Macedo
__BRA__	22	PI	2204204	Francisco Santos
__BRA__	22	PI	2204303	Fronteiras
__BRA__	22	PI	2204352	Geminiano
__BRA__	22	PI	2204402	Gilbués
__BRA__	22	PI	2204501	Guadalupe
__BRA__	22	PI	2204550	Guaribas
__BRA__	22	PI	2204600	Hugo Napoleão
__BRA__	22	PI	2204659	Ilha Grande
__BRA__	22	PI	2204709	Inhuma
__BRA__	22	PI	2204808	Ipiranga do Piauí
__BRA__	22	PI	2204907	Isaías Coelho
__BRA__	22	PI	2205003	Itainópolis
__BRA__	22	PI	2205102	Itaueira
__BRA__	22	PI	2205151	Jacobina do Piauí
__BRA__	22	PI	2205201	Jaicós
__BRA__	22	PI	2205250	Jardim do Mulato
__BRA__	22	PI	2205276	Jatobá do Piauí
__BRA__	22	PI	2205300	Jerumenha
__BRA__	22	PI	2205359	João Costa
__BRA__	22	PI	2205409	Joaquim Pires
__BRA__	22	PI	2205458	Joca Marques
__BRA__	22	PI	2205508	José de Freitas
__BRA__	22	PI	2205516	Juazeiro do Piauí
__BRA__	22	PI	2205524	Júlio Borges
__BRA__	22	PI	2205532	Jurema
__BRA__	22	PI	2205557	Lagoa Alegre
__BRA__	22	PI	2205573	Lagoa de São Francisco
__BRA__	22	PI	2205565	Lagoa do Barro do Piauí
__BRA__	22	PI	2205581	Lagoa do Piauí
__BRA__	22	PI	2205599	Lagoa do Sítio
__BRA__	22	PI	2205540	Lagoinha do Piauí
__BRA__	22	PI	2205607	Landri Sales
__BRA__	22	PI	2205706	Luís Correia
__BRA__	22	PI	2205805	Luzilândia
__BRA__	22	PI	2205854	Madeiro
__BRA__	22	PI	2205904	Manoel Emídio
__BRA__	22	PI	2205953	Marcolândia
__BRA__	22	PI	2206001	Marcos Parente
__BRA__	22	PI	2206050	Massapê do Piauí
__BRA__	22	PI	2206100	Matias Olímpio
__BRA__	22	PI	2206209	Miguel Alves
__BRA__	22	PI	2206308	Miguel Leão
__BRA__	22	PI	2206357	Milton Brandão
__BRA__	22	PI	2206407	Monsenhor Gil
__BRA__	22	PI	2206506	Monsenhor Hipólito
__BRA__	22	PI	2206605	Monte Alegre do Piauí
__BRA__	22	PI	2206654	Morro Cabeça no Tempo
__BRA__	22	PI	2206670	Morro do Chapéu do Piauí
__BRA__	22	PI	2206696	Murici dos Portelas
__BRA__	22	PI	2206704	Nazaré do Piauí
__BRA__	22	PI	2206720	Nazária
__BRA__	22	PI	2206753	Nossa Senhora de Nazaré
__BRA__	22	PI	2206803	Nossa Senhora dos Remédios
__BRA__	22	PI	2207959	Nova Santa Rita
__BRA__	22	PI	2206902	Novo Oriente do Piauí
__BRA__	22	PI	2206951	Novo Santo Antônio
__BRA__	22	PI	2207009	Oeiras
__BRA__	22	PI	2207108	Olho D'Água do Piauí
__BRA__	22	PI	2207207	Padre Marcos
__BRA__	22	PI	2207306	Paes Landim
__BRA__	22	PI	2207355	Pajeú do Piauí
__BRA__	22	PI	2207405	Palmeira do Piauí
__BRA__	22	PI	2207504	Palmeirais
__BRA__	22	PI	2207553	Paquetá
__BRA__	22	PI	2207603	Parnaguá
__BRA__	22	PI	2207702	Parnaíba
__BRA__	22	PI	2207751	Passagem Franca do Piauí
__BRA__	22	PI	2207777	Patos do Piauí
__BRA__	22	PI	2207793	Pau D'Arco do Piauí
__BRA__	22	PI	2207801	Paulistana
__BRA__	22	PI	2207850	Pavussu
__BRA__	22	PI	2207900	Pedro II
__BRA__	22	PI	2207934	Pedro Laurentino
__BRA__	22	PI	2208007	Picos
__BRA__	22	PI	2208106	Pimenteiras
__BRA__	22	PI	2208205	Pio IX
__BRA__	22	PI	2208304	Piracuruca
__BRA__	22	PI	2208403	Piripiri
__BRA__	22	PI	2208502	Porto
__BRA__	22	PI	2208551	Porto Alegre do Piauí
__BRA__	22	PI	2208601	Prata do Piauí
__BRA__	22	PI	2208650	Queimada Nova
__BRA__	22	PI	2208700	Redenção do Gurguéia
__BRA__	22	PI	2208809	Regeneração
__BRA__	22	PI	2208858	Riacho Frio
__BRA__	22	PI	2208874	Ribeira do Piauí
__BRA__	22	PI	2208908	Ribeiro Gonçalves
__BRA__	22	PI	2209005	Rio Grande do Piauí
__BRA__	22	PI	2209104	Santa Cruz do Piauí
__BRA__	22	PI	2209153	Santa Cruz dos Milagres
__BRA__	22	PI	2209203	Santa Filomena
__BRA__	22	PI	2209302	Santa Luz
__BRA__	22	PI	2209377	Santa Rosa do Piauí
__BRA__	22	PI	2209351	Santana do Piauí
__BRA__	22	PI	2209401	Santo Antônio de Lisboa
__BRA__	22	PI	2209450	Santo Antônio dos Milagres
__BRA__	22	PI	2209500	Santo Inácio do Piauí
__BRA__	22	PI	2209559	São Braz do Piauí
__BRA__	22	PI	2209609	São Félix do Piauí
__BRA__	22	PI	2209658	São Francisco de Assis do Piauí
__BRA__	22	PI	2209708	São Francisco do Piauí
__BRA__	22	PI	2209757	São Gonçalo do Gurguéia
__BRA__	22	PI	2209807	São Gonçalo do Piauí
__BRA__	22	PI	2209856	São João da Canabrava
__BRA__	22	PI	2209872	São João da Fronteira
__BRA__	22	PI	2209906	São João da Serra
__BRA__	22	PI	2209955	São João da Varjota
__BRA__	22	PI	2209971	São João do Arraial
__BRA__	22	PI	2210003	São João do Piauí
__BRA__	22	PI	2210052	São José do Divino
__BRA__	22	PI	2210102	São José do Peixe
__BRA__	22	PI	2210201	São José do Piauí
__BRA__	22	PI	2210300	São Julião
__BRA__	22	PI	2210359	São Lourenço do Piauí
__BRA__	22	PI	2210375	São Luis do Piauí
__BRA__	22	PI	2210383	São Miguel da Baixa Grande
__BRA__	22	PI	2210391	São Miguel do Fidalgo
__BRA__	22	PI	2210409	São Miguel do Tapuio
__BRA__	22	PI	2210508	São Pedro do Piauí
__BRA__	22	PI	2210607	São Raimundo Nonato
__BRA__	22	PI	2210623	Sebastião Barros
__BRA__	22	PI	2210631	Sebastião Leal
__BRA__	22	PI	2210656	Sigefredo Pacheco
__BRA__	22	PI	2210706	Simões
__BRA__	22	PI	2210805	Simplício Mendes
__BRA__	22	PI	2210904	Socorro do Piauí
__BRA__	22	PI	2210938	Sussuapara
__BRA__	22	PI	2210953	Tamboril do Piauí
__BRA__	22	PI	2210979	Tanque do Piauí
__BRA__	22	PI	2211001	Teresina
__BRA__	22	PI	2211100	União
__BRA__	22	PI	2211209	Uruçuí
__BRA__	22	PI	2211308	Valença do Piauí
__BRA__	22	PI	2211357	Várzea Branca
__BRA__	22	PI	2211407	Várzea Grande
__BRA__	22	PI	2211506	Vera Mendes
__BRA__	22	PI	2211605	Vila Nova do Piauí
__BRA__	22	PI	2211704	Wall Ferraz
__BRA__	25	PB	2500106	Água Branca
__BRA__	25	PB	2500205	Aguiar
__BRA__	25	PB	2500304	Alagoa Grande
__BRA__	25	PB	2500403	Alagoa Nova
__BRA__	25	PB	2500502	Alagoinha
__BRA__	25	PB	2500536	Alcantil
__BRA__	25	PB	2500577	Algodão de Jandaíra
__BRA__	25	PB	2500601	Alhandra
__BRA__	25	PB	2500734	Amparo
__BRA__	25	PB	2500775	Aparecida
__BRA__	25	PB	2500809	Araçagi
__BRA__	25	PB	2500908	Arara
__BRA__	25	PB	2501005	Araruna
__BRA__	25	PB	2501104	Areia
__BRA__	25	PB	2501153	Areia de Baraúnas
__BRA__	25	PB	2501203	Areial
__BRA__	25	PB	2501302	Aroeiras
__BRA__	25	PB	2501351	Assunção
__BRA__	25	PB	2501401	Baía da Traição
__BRA__	25	PB	2501500	Bananeiras
__BRA__	25	PB	2501534	Baraúna
__BRA__	25	PB	2501609	Barra de Santa Rosa
__BRA__	25	PB	2501575	Barra de Santana
__BRA__	25	PB	2501708	Barra de São Miguel
__BRA__	25	PB	2501807	Bayeux
__BRA__	25	PB	2501906	Belém
__BRA__	25	PB	2502003	Belém do Brejo do Cruz
__BRA__	25	PB	2502052	Bernardino Batista
__BRA__	25	PB	2502102	Boa Ventura
__BRA__	25	PB	2502151	Boa Vista
__BRA__	25	PB	2502201	Bom Jesus
__BRA__	25	PB	2502300	Bom Sucesso
__BRA__	25	PB	2502409	Bonito de Santa Fé
__BRA__	25	PB	2502508	Boqueirão
__BRA__	25	PB	2502706	Borborema
__BRA__	25	PB	2502805	Brejo do Cruz
__BRA__	25	PB	2502904	Brejo dos Santos
__BRA__	25	PB	2503001	Caaporã
__BRA__	25	PB	2503100	Cabaceiras
__BRA__	25	PB	2503209	Cabedelo
__BRA__	25	PB	2503308	Cachoeira dos Índios
__BRA__	25	PB	2503407	Cacimba de Areia
__BRA__	25	PB	2503506	Cacimba de Dentro
__BRA__	25	PB	2503555	Cacimbas
__BRA__	25	PB	2503605	Caiçara
__BRA__	25	PB	2503704	Cajazeiras
__BRA__	25	PB	2503753	Cajazeirinhas
__BRA__	25	PB	2503803	Caldas Brandão
__BRA__	25	PB	2503902	Camalaú
__BRA__	25	PB	2504009	Campina Grande
__BRA__	25	PB	2516409	Campo de Santana
__BRA__	25	PB	2504033	Capim
__BRA__	25	PB	2504074	Caraúbas
__BRA__	25	PB	2504108	Carrapateira
__BRA__	25	PB	2504157	Casserengue
__BRA__	25	PB	2504207	Catingueira
__BRA__	25	PB	2504306	Catolé do Rocha
__BRA__	25	PB	2504355	Caturité
__BRA__	25	PB	2504405	Conceição
__BRA__	25	PB	2504504	Condado
__BRA__	25	PB	2504603	Conde
__BRA__	25	PB	2504702	Congo
__BRA__	25	PB	2504801	Coremas
__BRA__	25	PB	2504850	Coxixola
__BRA__	25	PB	2504900	Cruz do Espírito Santo
__BRA__	25	PB	2505006	Cubati
__BRA__	25	PB	2505105	Cuité
__BRA__	25	PB	2505238	Cuité de Mamanguape
__BRA__	25	PB	2505204	Cuitegi
__BRA__	25	PB	2505279	Curral de Cima
__BRA__	25	PB	2505303	Curral Velho
__BRA__	25	PB	2505352	Damião
__BRA__	25	PB	2505402	Desterro
__BRA__	25	PB	2505600	Diamante
__BRA__	25	PB	2505709	Dona Inês
__BRA__	25	PB	2505808	Duas Estradas
__BRA__	25	PB	2505907	Emas
__BRA__	25	PB	2506004	Esperança
__BRA__	25	PB	2506103	Fagundes
__BRA__	25	PB	2506202	Frei Martinho
__BRA__	25	PB	2506251	Gado Bravo
__BRA__	25	PB	2506301	Guarabira
__BRA__	25	PB	2506400	Gurinhém
__BRA__	25	PB	2506509	Gurjão
__BRA__	25	PB	2506608	Ibiara
__BRA__	25	PB	2502607	Igaracy
__BRA__	25	PB	2506707	Imaculada
__BRA__	25	PB	2506806	Ingá
__BRA__	25	PB	2506905	Itabaiana
__BRA__	25	PB	2507002	Itaporanga
__BRA__	25	PB	2507101	Itapororoca
__BRA__	25	PB	2507200	Itatuba
__BRA__	25	PB	2507309	Jacaraú
__BRA__	25	PB	2507408	Jericó
__BRA__	25	PB	2507507	João Pessoa
__BRA__	25	PB	2507606	Juarez Távora
__BRA__	25	PB	2507705	Juazeirinho
__BRA__	25	PB	2507804	Junco do Seridó
__BRA__	25	PB	2507903	Juripiranga
__BRA__	25	PB	2508000	Juru
__BRA__	25	PB	2508109	Lagoa
__BRA__	25	PB	2508208	Lagoa de Dentro
__BRA__	25	PB	2508307	Lagoa Seca
__BRA__	25	PB	2508406	Lastro
__BRA__	25	PB	2508505	Livramento
__BRA__	25	PB	2508554	Logradouro
__BRA__	25	PB	2508604	Lucena
__BRA__	25	PB	2508703	Mãe d'Água
__BRA__	25	PB	2508802	Malta
__BRA__	25	PB	2508901	Mamanguape
__BRA__	25	PB	2509008	Manaíra
__BRA__	25	PB	2509057	Marcação
__BRA__	25	PB	2509107	Mari
__BRA__	25	PB	2509156	Marizópolis
__BRA__	25	PB	2509206	Massaranduba
__BRA__	25	PB	2509305	Mataraca
__BRA__	25	PB	2509339	Matinhas
__BRA__	25	PB	2509370	Mato Grosso
__BRA__	25	PB	2509396	Maturéia
__BRA__	25	PB	2509404	Mogeiro
__BRA__	25	PB	2509503	Montadas
__BRA__	25	PB	2509602	Monte Horebe
__BRA__	25	PB	2509701	Monteiro
__BRA__	25	PB	2509800	Mulungu
__BRA__	25	PB	2509909	Natuba
__BRA__	25	PB	2510006	Nazarezinho
__BRA__	25	PB	2510105	Nova Floresta
__BRA__	25	PB	2510204	Nova Olinda
__BRA__	25	PB	2510303	Nova Palmeira
__BRA__	25	PB	2510402	Olho d'Água
__BRA__	25	PB	2510501	Olivedos
__BRA__	25	PB	2510600	Ouro Velho
__BRA__	25	PB	2510659	Parari
__BRA__	25	PB	2510709	Passagem
__BRA__	25	PB	2510808	Patos
__BRA__	25	PB	2510907	Paulista
__BRA__	25	PB	2511004	Pedra Branca
__BRA__	25	PB	2511103	Pedra Lavrada
__BRA__	25	PB	2511202	Pedras de Fogo
__BRA__	25	PB	2512721	Pedro Régis
__BRA__	25	PB	2511301	Piancó
__BRA__	25	PB	2511400	Picuí
__BRA__	25	PB	2511509	Pilar
__BRA__	25	PB	2511608	Pilões
__BRA__	25	PB	2511707	Pilõezinhos
__BRA__	25	PB	2511806	Pirpirituba
__BRA__	25	PB	2511905	Pitimbu
__BRA__	25	PB	2512002	Pocinhos
__BRA__	25	PB	2512036	Poço Dantas
__BRA__	25	PB	2512077	Poço de José de Moura
__BRA__	25	PB	2512101	Pombal
__BRA__	25	PB	2512200	Prata
__BRA__	25	PB	2512309	Princesa Isabel
__BRA__	25	PB	2512408	Puxinanã
__BRA__	25	PB	2512507	Queimadas
__BRA__	25	PB	2512606	Quixabá
__BRA__	25	PB	2512705	Remígio
__BRA__	25	PB	2512747	Riachão
__BRA__	25	PB	2512754	Riachão do Bacamarte
__BRA__	25	PB	2512762	Riachão do Poço
__BRA__	25	PB	2512788	Riacho de Santo Antônio
__BRA__	25	PB	2512804	Riacho dos Cavalos
__BRA__	25	PB	2512903	Rio Tinto
__BRA__	25	PB	2513000	Salgadinho
__BRA__	25	PB	2513109	Salgado de São Félix
__BRA__	25	PB	2513158	Santa Cecília
__BRA__	25	PB	2513208	Santa Cruz
__BRA__	25	PB	2513307	Santa Helena
__BRA__	25	PB	2513356	Santa Inês
__BRA__	25	PB	2513406	Santa Luzia
__BRA__	25	PB	2513703	Santa Rita
__BRA__	25	PB	2513802	Santa Teresinha
__BRA__	25	PB	2513505	Santana de Mangueira
__BRA__	25	PB	2513604	Santana dos Garrotes
__BRA__	25	PB	2513653	Santarém
__BRA__	25	PB	2513851	Santo André
__BRA__	25	PB	2513927	São Bentinho
__BRA__	25	PB	2513901	São Bento
__BRA__	25	PB	2513968	São Domingos de Pombal
__BRA__	25	PB	2513943	São Domingos do Cariri
__BRA__	25	PB	2513984	São Francisco
__BRA__	25	PB	2514008	São João do Cariri
__BRA__	25	PB	2500700	São João do Rio do Peixe
__BRA__	25	PB	2514107	São João do Tigre
__BRA__	25	PB	2514206	São José da Lagoa Tapada
__BRA__	25	PB	2514305	São José de Caiana
__BRA__	25	PB	2514404	São José de Espinharas
__BRA__	25	PB	2514503	São José de Piranhas
__BRA__	25	PB	2514552	São José de Princesa
__BRA__	25	PB	2514602	São José do Bonfim
__BRA__	25	PB	2514651	São José do Brejo do Cruz
__BRA__	25	PB	2514701	São José do Sabugi
__BRA__	25	PB	2514800	São José dos Cordeiros
__BRA__	25	PB	2514453	São José dos Ramos
__BRA__	25	PB	2514909	São Mamede
__BRA__	25	PB	2515005	São Miguel de Taipu
__BRA__	25	PB	2515104	São Sebastião de Lagoa de Roça
__BRA__	25	PB	2515203	São Sebastião do Umbuzeiro
__BRA__	25	PB	2515302	Sapé
__BRA__	25	PB	2515401	Seridó
__BRA__	25	PB	2515500	Serra Branca
__BRA__	25	PB	2515609	Serra da Raiz
__BRA__	25	PB	2515708	Serra Grande
__BRA__	25	PB	2515807	Serra Redonda
__BRA__	25	PB	2515906	Serraria
__BRA__	25	PB	2515930	Sertãozinho
__BRA__	25	PB	2515971	Sobrado
__BRA__	25	PB	2516003	Solânea
__BRA__	25	PB	2516102	Soledade
__BRA__	25	PB	2516151	Sossêgo
__BRA__	25	PB	2516201	Sousa
__BRA__	25	PB	2516300	Sumé
__BRA__	25	PB	2516508	Taperoá
__BRA__	25	PB	2516607	Tavares
__BRA__	25	PB	2516706	Teixeira
__BRA__	25	PB	2516755	Tenório
__BRA__	25	PB	2516805	Triunfo
__BRA__	25	PB	2516904	Uiraúna
__BRA__	25	PB	2517001	Umbuzeiro
__BRA__	25	PB	2517100	Várzea
__BRA__	25	PB	2517209	Vieirópolis
__BRA__	25	PB	2505501	Vista Serrana
__BRA__	25	PB	2517407	Zabelê
__BRA__	52	GO	5200050	Abadia de Goiás
__BRA__	52	GO	5200100	Abadiânia
__BRA__	52	GO	5200134	Acreúna
__BRA__	52	GO	5200159	Adelândia
__BRA__	52	GO	5200175	Água Fria de Goiás
__BRA__	52	GO	5200209	Água Limpa
__BRA__	52	GO	5200258	Águas Lindas de Goiás
__BRA__	52	GO	5200308	Alexânia
__BRA__	52	GO	5200506	Aloândia
__BRA__	52	GO	5200555	Alto Horizonte
__BRA__	52	GO	5200605	Alto Paraíso de Goiás
__BRA__	52	GO	5200803	Alvorada do Norte
__BRA__	52	GO	5200829	Amaralina
__BRA__	52	GO	5200852	Americano do Brasil
__BRA__	52	GO	5200902	Amorinópolis
__BRA__	52	GO	5201108	Anápolis
__BRA__	52	GO	5201207	Anhanguera
__BRA__	52	GO	5201306	Anicuns
__BRA__	52	GO	5201405	Aparecida de Goiânia
__BRA__	52	GO	5201454	Aparecida do Rio Doce
__BRA__	52	GO	5201504	Aporé
__BRA__	52	GO	5201603	Araçu
__BRA__	52	GO	5201702	Aragarças
__BRA__	52	GO	5201801	Aragoiânia
__BRA__	52	GO	5202155	Araguapaz
__BRA__	52	GO	5202353	Arenópolis
__BRA__	52	GO	5202502	Aruanã
__BRA__	52	GO	5202601	Aurilândia
__BRA__	52	GO	5202809	Avelinópolis
__BRA__	52	GO	5203104	Baliza
__BRA__	52	GO	5203203	Barro Alto
__BRA__	52	GO	5203302	Bela Vista de Goiás
__BRA__	52	GO	5203401	Bom Jardim de Goiás
__BRA__	52	GO	5203500	Bom Jesus de Goiás
__BRA__	52	GO	5203559	Bonfinópolis
__BRA__	52	GO	5203575	Bonópolis
__BRA__	52	GO	5203609	Brazabrantes
__BRA__	52	GO	5203807	Britânia
__BRA__	52	GO	5203906	Buriti Alegre
__BRA__	52	GO	5203939	Buriti de Goiás
__BRA__	52	GO	5203962	Buritinópolis
__BRA__	52	GO	5204003	Cabeceiras
__BRA__	52	GO	5204102	Cachoeira Alta
__BRA__	52	GO	5204201	Cachoeira de Goiás
__BRA__	52	GO	5204250	Cachoeira Dourada
__BRA__	52	GO	5204300	Caçu
__BRA__	52	GO	5204409	Caiapônia
__BRA__	52	GO	5204508	Caldas Novas
__BRA__	52	GO	5204557	Caldazinha
__BRA__	52	GO	5204607	Campestre de Goiás
__BRA__	52	GO	5204656	Campinaçu
__BRA__	52	GO	5204706	Campinorte
__BRA__	52	GO	5204805	Campo Alegre de Goiás
__BRA__	52	GO	5204854	Campo Limpo de Goiás
__BRA__	52	GO	5204904	Campos Belos
__BRA__	52	GO	5204953	Campos Verdes
__BRA__	52	GO	5205000	Carmo do Rio Verde
__BRA__	52	GO	5205059	Castelândia
__BRA__	52	GO	5205109	Catalão
__BRA__	52	GO	5205208	Caturaí
__BRA__	52	GO	5205307	Cavalcante
__BRA__	52	GO	5205406	Ceres
__BRA__	52	GO	5205455	Cezarina
__BRA__	52	GO	5205471	Chapadão do Céu
__BRA__	52	GO	5205497	Cidade Ocidental
__BRA__	52	GO	5205513	Cocalzinho de Goiás
__BRA__	52	GO	5205521	Colinas do Sul
__BRA__	52	GO	5205703	Córrego do Ouro
__BRA__	52	GO	5205802	Corumbá de Goiás
__BRA__	52	GO	5205901	Corumbaíba
__BRA__	52	GO	5206206	Cristalina
__BRA__	52	GO	5206305	Cristianópolis
__BRA__	52	GO	5206404	Crixás
__BRA__	52	GO	5206503	Cromínia
__BRA__	52	GO	5206602	Cumari
__BRA__	52	GO	5206701	Damianópolis
__BRA__	52	GO	5206800	Damolândia
__BRA__	52	GO	5206909	Davinópolis
__BRA__	52	GO	5207105	Diorama
__BRA__	52	GO	5208301	Divinópolis de Goiás
__BRA__	52	GO	5207253	Doverlândia
__BRA__	52	GO	5207352	Edealina
__BRA__	52	GO	5207402	Edéia
__BRA__	52	GO	5207501	Estrela do Norte
__BRA__	52	GO	5207535	Faina
__BRA__	52	GO	5207600	Fazenda Nova
__BRA__	52	GO	5207808	Firminópolis
__BRA__	52	GO	5207907	Flores de Goiás
__BRA__	52	GO	5208004	Formosa
__BRA__	52	GO	5208103	Formoso
__BRA__	52	GO	5208152	Gameleira de Goiás
__BRA__	52	GO	5208400	Goianápolis
__BRA__	52	GO	5208509	Goiandira
__BRA__	52	GO	5208608	Goianésia
__BRA__	52	GO	5208707	Goiânia
__BRA__	52	GO	5208806	Goianira
__BRA__	52	GO	5208905	Goiás
__BRA__	52	GO	5209101	Goiatuba
__BRA__	52	GO	5209150	Gouvelândia
__BRA__	52	GO	5209200	Guapó
__BRA__	52	GO	5209291	Guaraíta
__BRA__	52	GO	5209408	Guarani de Goiás
__BRA__	52	GO	5209457	Guarinos
__BRA__	52	GO	5209606	Heitoraí
__BRA__	52	GO	5209705	Hidrolândia
__BRA__	52	GO	5209804	Hidrolina
__BRA__	52	GO	5209903	Iaciara
__BRA__	52	GO	5209937	Inaciolândia
__BRA__	52	GO	5209952	Indiara
__BRA__	52	GO	5210000	Inhumas
__BRA__	52	GO	5210109	Ipameri
__BRA__	52	GO	5210158	Ipiranga de Goiás
__BRA__	52	GO	5210208	Iporá
__BRA__	52	GO	5210307	Israelândia
__BRA__	52	GO	5210406	Itaberaí
__BRA__	52	GO	5210562	Itaguari
__BRA__	52	GO	5210604	Itaguaru
__BRA__	52	GO	5210802	Itajá
__BRA__	52	GO	5210901	Itapaci
__BRA__	52	GO	5211008	Itapirapuã
__BRA__	52	GO	5211206	Itapuranga
__BRA__	52	GO	5211305	Itarumã
__BRA__	52	GO	5211404	Itauçu
__BRA__	52	GO	5211503	Itumbiara
__BRA__	52	GO	5211602	Ivolândia
__BRA__	52	GO	5211701	Jandaia
__BRA__	52	GO	5211800	Jaraguá
__BRA__	52	GO	5211909	Jataí
__BRA__	52	GO	5212006	Jaupaci
__BRA__	52	GO	5212055	Jesúpolis
__BRA__	52	GO	5212105	Joviânia
__BRA__	52	GO	5212204	Jussara
__BRA__	52	GO	5212253	Lagoa Santa
__BRA__	52	GO	5212303	Leopoldo de Bulhões
__BRA__	52	GO	5212501	Luziânia
__BRA__	52	GO	5212600	Mairipotaba
__BRA__	52	GO	5212709	Mambaí
__BRA__	52	GO	5212808	Mara Rosa
__BRA__	52	GO	5212907	Marzagão
__BRA__	52	GO	5212956	Matrinchã
__BRA__	52	GO	5213004	Maurilândia
__BRA__	52	GO	5213053	Mimoso de Goiás
__BRA__	52	GO	5213087	Minaçu
__BRA__	52	GO	5213103	Mineiros
__BRA__	52	GO	5213400	Moiporá
__BRA__	52	GO	5213509	Monte Alegre de Goiás
__BRA__	52	GO	5213707	Montes Claros de Goiás
__BRA__	52	GO	5213756	Montividiu
__BRA__	52	GO	5213772	Montividiu do Norte
__BRA__	52	GO	5213806	Morrinhos
__BRA__	52	GO	5213855	Morro Agudo de Goiás
__BRA__	52	GO	5213905	Mossâmedes
__BRA__	52	GO	5214002	Mozarlândia
__BRA__	52	GO	5214051	Mundo Novo
__BRA__	52	GO	5214101	Mutunópolis
__BRA__	52	GO	5214408	Nazário
__BRA__	52	GO	5214507	Nerópolis
__BRA__	52	GO	5214606	Niquelândia
__BRA__	52	GO	5214705	Nova América
__BRA__	52	GO	5214804	Nova Aurora
__BRA__	52	GO	5214838	Nova Crixás
__BRA__	52	GO	5214861	Nova Glória
__BRA__	52	GO	5214879	Nova Iguaçu de Goiás
__BRA__	52	GO	5214903	Nova Roma
__BRA__	52	GO	5215009	Nova Veneza
__BRA__	52	GO	5215207	Novo Brasil
__BRA__	52	GO	5215231	Novo Gama
__BRA__	52	GO	5215256	Novo Planalto
__BRA__	52	GO	5215306	Orizona
__BRA__	52	GO	5215405	Ouro Verde de Goiás
__BRA__	52	GO	5215504	Ouvidor
__BRA__	52	GO	5215603	Padre Bernardo
__BRA__	52	GO	5215652	Palestina de Goiás
__BRA__	52	GO	5215702	Palmeiras de Goiás
__BRA__	52	GO	5215801	Palmelo
__BRA__	52	GO	5215900	Palminópolis
__BRA__	52	GO	5216007	Panamá
__BRA__	52	GO	5216304	Paranaiguara
__BRA__	52	GO	5216403	Paraúna
__BRA__	52	GO	5216452	Perolândia
__BRA__	52	GO	5216809	Petrolina de Goiás
__BRA__	52	GO	5216908	Pilar de Goiás
__BRA__	52	GO	5217104	Piracanjuba
__BRA__	52	GO	5217203	Piranhas
__BRA__	52	GO	5217302	Pirenópolis
__BRA__	52	GO	5217401	Pires do Rio
__BRA__	52	GO	5217609	Planaltina
__BRA__	52	GO	5217708	Pontalina
__BRA__	52	GO	5218003	Porangatu
__BRA__	52	GO	5218052	Porteirão
__BRA__	52	GO	5218102	Portelândia
__BRA__	52	GO	5218300	Posse
__BRA__	52	GO	5218391	Professor Jamil
__BRA__	52	GO	5218508	Quirinópolis
__BRA__	52	GO	5218607	Rialma
__BRA__	52	GO	5218706	Rianápolis
__BRA__	52	GO	5218789	Rio Quente
__BRA__	52	GO	5218805	Rio Verde
__BRA__	52	GO	5218904	Rubiataba
__BRA__	52	GO	5219001	Sanclerlândia
__BRA__	52	GO	5219100	Santa Bárbara de Goiás
__BRA__	52	GO	5219209	Santa Cruz de Goiás
__BRA__	52	GO	5219258	Santa Fé de Goiás
__BRA__	52	GO	5219308	Santa Helena de Goiás
__BRA__	52	GO	5219357	Santa Isabel
__BRA__	52	GO	5219407	Santa Rita do Araguaia
__BRA__	52	GO	5219456	Santa Rita do Novo Destino
__BRA__	52	GO	5219506	Santa Rosa de Goiás
__BRA__	52	GO	5219605	Santa Tereza de Goiás
__BRA__	52	GO	5219704	Santa Terezinha de Goiás
__BRA__	52	GO	5219712	Santo Antônio da Barra
__BRA__	52	GO	5219738	Santo Antônio de Goiás
__BRA__	52	GO	5219753	Santo Antônio do Descoberto
__BRA__	52	GO	5219803	São Domingos
__BRA__	52	GO	5219902	São Francisco de Goiás
__BRA__	52	GO	5220058	São João da Paraúna
__BRA__	52	GO	5220009	São João d'Aliança
__BRA__	52	GO	5220108	São Luís de Montes Belos
__BRA__	52	GO	5220157	São Luíz do Norte
__BRA__	52	GO	5220207	São Miguel do Araguaia
__BRA__	52	GO	5220264	São Miguel do Passa Quatro
__BRA__	52	GO	5220280	São Patrício
__BRA__	52	GO	5220405	São Simão
__BRA__	52	GO	5220454	Senador Canedo
__BRA__	52	GO	5220504	Serranópolis
__BRA__	52	GO	5220603	Silvânia
__BRA__	52	GO	5220686	Simolândia
__BRA__	52	GO	5220702	Sítio d'Abadia
__BRA__	52	GO	5221007	Taquaral de Goiás
__BRA__	52	GO	5221080	Teresina de Goiás
__BRA__	52	GO	5221197	Terezópolis de Goiás
__BRA__	52	GO	5221304	Três Ranchos
__BRA__	52	GO	5221403	Trindade
__BRA__	52	GO	5221452	Trombas
__BRA__	52	GO	5221502	Turvânia
__BRA__	52	GO	5221551	Turvelândia
__BRA__	52	GO	5221577	Uirapuru
__BRA__	52	GO	5221601	Uruaçu
__BRA__	52	GO	5221700	Uruana
__BRA__	52	GO	5221809	Urutaí
__BRA__	52	GO	5221858	Valparaíso de Goiás
__BRA__	52	GO	5221908	Varjão
__BRA__	52	GO	5222005	Vianópolis
__BRA__	52	GO	5222054	Vicentinópolis
__BRA__	52	GO	5222203	Vila Boa
__BRA__	52	GO	5222302	Vila Propício
__BRA__	42	SC	4200051	Abdon Batista
__BRA__	42	SC	4200101	Abelardo Luz
__BRA__	42	SC	4200200	Agrolândia
__BRA__	42	SC	4200309	Agronômica
__BRA__	42	SC	4200408	Água Doce
__BRA__	42	SC	4200507	Águas de Chapecó
__BRA__	42	SC	4200556	Águas Frias
__BRA__	42	SC	4200606	Águas Mornas
__BRA__	42	SC	4200705	Alfredo Wagner
__BRA__	42	SC	4200754	Alto Bela Vista
__BRA__	42	SC	4200804	Anchieta
__BRA__	42	SC	4200903	Angelina
__BRA__	42	SC	4201000	Anita Garibaldi
__BRA__	42	SC	4201109	Anitápolis
__BRA__	42	SC	4201208	Antônio Carlos
__BRA__	42	SC	4201257	Apiúna
__BRA__	42	SC	4201273	Arabutã
__BRA__	42	SC	4201307	Araquari
__BRA__	42	SC	4201406	Araranguá
__BRA__	42	SC	4201505	Armazém
__BRA__	42	SC	4201604	Arroio Trinta
__BRA__	42	SC	4201653	Arvoredo
__BRA__	42	SC	4201703	Ascurra
__BRA__	42	SC	4201802	Atalanta
__BRA__	42	SC	4201901	Aurora
__BRA__	42	SC	4201950	Balneário Arroio do Silva
__BRA__	42	SC	4202057	Balneário Barra do Sul
__BRA__	42	SC	4202008	Balneário Camboriú
__BRA__	42	SC	4202073	Balneário Gaivota
__BRA__	42	SC	4212809	Balneário Piçarras
__BRA__	42	SC	4202081	Bandeirante
__BRA__	42	SC	4202099	Barra Bonita
__BRA__	42	SC	4202107	Barra Velha
__BRA__	42	SC	4202131	Bela Vista do Toldo
__BRA__	42	SC	4202156	Belmonte
__BRA__	42	SC	4202206	Benedito Novo
__BRA__	42	SC	4202305	Biguaçu
__BRA__	42	SC	4202404	Blumenau
__BRA__	42	SC	4202438	Bocaina do Sul
__BRA__	42	SC	4202503	Bom Jardim da Serra
__BRA__	42	SC	4202537	Bom Jesus
__BRA__	42	SC	4202578	Bom Jesus do Oeste
__BRA__	42	SC	4202602	Bom Retiro
__BRA__	42	SC	4202453	Bombinhas
__BRA__	42	SC	4202701	Botuverá
__BRA__	42	SC	4202800	Braço do Norte
__BRA__	42	SC	4202859	Braço do Trombudo
__BRA__	42	SC	4202875	Brunópolis
__BRA__	42	SC	4202909	Brusque
__BRA__	42	SC	4203006	Caçador
__BRA__	42	SC	4203105	Caibi
__BRA__	42	SC	4203154	Calmon
__BRA__	42	SC	4203204	Camboriú
__BRA__	42	SC	4203303	Campo Alegre
__BRA__	42	SC	4203402	Campo Belo do Sul
__BRA__	42	SC	4203501	Campo Erê
__BRA__	42	SC	4203600	Campos Novos
__BRA__	42	SC	4203709	Canelinha
__BRA__	42	SC	4203808	Canoinhas
__BRA__	42	SC	4203253	Capão Alto
__BRA__	42	SC	4203907	Capinzal
__BRA__	42	SC	4203956	Capivari de Baixo
__BRA__	42	SC	4204004	Catanduvas
__BRA__	42	SC	4204103	Caxambu do Sul
__BRA__	42	SC	4204152	Celso Ramos
__BRA__	42	SC	4204178	Cerro Negro
__BRA__	42	SC	4204194	Chapadão do Lageado
__BRA__	42	SC	4204202	Chapecó
__BRA__	42	SC	4204251	Cocal do Sul
__BRA__	42	SC	4204301	Concórdia
__BRA__	42	SC	4204350	Cordilheira Alta
__BRA__	42	SC	4204400	Coronel Freitas
__BRA__	42	SC	4204459	Coronel Martins
__BRA__	42	SC	4204558	Correia Pinto
__BRA__	42	SC	4204509	Corupá
__BRA__	42	SC	4204608	Criciúma
__BRA__	42	SC	4204707	Cunha Porã
__BRA__	42	SC	4204756	Cunhataí
__BRA__	42	SC	4204806	Curitibanos
__BRA__	42	SC	4204905	Descanso
__BRA__	42	SC	4205001	Dionísio Cerqueira
__BRA__	42	SC	4205100	Dona Emma
__BRA__	42	SC	4205159	Doutor Pedrinho
__BRA__	42	SC	4205175	Entre Rios
__BRA__	42	SC	4205191	Ermo
__BRA__	42	SC	4205209	Erval Velho
__BRA__	42	SC	4205308	Faxinal dos Guedes
__BRA__	42	SC	4205357	Flor do Sertão
__BRA__	42	SC	4205407	Florianópolis
__BRA__	42	SC	4205431	Formosa do Sul
__BRA__	42	SC	4205456	Forquilhinha
__BRA__	42	SC	4205506	Fraiburgo
__BRA__	42	SC	4205555	Frei Rogério
__BRA__	42	SC	4205605	Galvão
__BRA__	42	SC	4205704	Garopaba
__BRA__	42	SC	4205803	Garuva
__BRA__	42	SC	4205902	Gaspar
__BRA__	42	SC	4206009	Governador Celso Ramos
__BRA__	42	SC	4206108	Grão Pará
__BRA__	42	SC	4206207	Gravatal
__BRA__	42	SC	4206306	Guabiruba
__BRA__	42	SC	4206405	Guaraciaba
__BRA__	42	SC	4206504	Guaramirim
__BRA__	42	SC	4206603	Guarujá do Sul
__BRA__	42	SC	4206652	Guatambú
__BRA__	42	SC	4206702	Herval d'Oeste
__BRA__	42	SC	4206751	Ibiam
__BRA__	42	SC	4206801	Ibicaré
__BRA__	42	SC	4206900	Ibirama
__BRA__	42	SC	4207007	Içara
__BRA__	42	SC	4207106	Ilhota
__BRA__	42	SC	4207205	Imaruí
__BRA__	42	SC	4207304	Imbituba
__BRA__	42	SC	4207403	Imbuia
__BRA__	42	SC	4207502	Indaial
__BRA__	42	SC	4207577	Iomerê
__BRA__	42	SC	4207601	Ipira
__BRA__	42	SC	4207650	Iporã do Oeste
__BRA__	42	SC	4207684	Ipuaçu
__BRA__	42	SC	4207700	Ipumirim
__BRA__	42	SC	4207759	Iraceminha
__BRA__	42	SC	4207809	Irani
__BRA__	42	SC	4207858	Irati
__BRA__	42	SC	4207908	Irineópolis
__BRA__	42	SC	4208005	Itá
__BRA__	42	SC	4208104	Itaiópolis
__BRA__	42	SC	4208203	Itajaí
__BRA__	42	SC	4208302	Itapema
__BRA__	42	SC	4208401	Itapiranga
__BRA__	42	SC	4208450	Itapoá
__BRA__	42	SC	4208500	Ituporanga
__BRA__	42	SC	4208609	Jaborá
__BRA__	42	SC	4208708	Jacinto Machado
__BRA__	42	SC	4208807	Jaguaruna
__BRA__	42	SC	4208906	Jaraguá do Sul
__BRA__	42	SC	4208955	Jardinópolis
__BRA__	42	SC	4209003	Joaçaba
__BRA__	42	SC	4209102	Joinville
__BRA__	42	SC	4209151	José Boiteux
__BRA__	42	SC	4209177	Jupiá
__BRA__	42	SC	4209201	Lacerdópolis
__BRA__	42	SC	4209300	Lages
__BRA__	42	SC	4209409	Laguna
__BRA__	42	SC	4209458	Lajeado Grande
__BRA__	42	SC	4209508	Laurentino
__BRA__	42	SC	4209607	Lauro Muller
__BRA__	42	SC	4209706	Lebon Régis
__BRA__	42	SC	4209805	Leoberto Leal
__BRA__	42	SC	4209854	Lindóia do Sul
__BRA__	42	SC	4209904	Lontras
__BRA__	42	SC	4210001	Luiz Alves
__BRA__	42	SC	4210035	Luzerna
__BRA__	42	SC	4210050	Macieira
__BRA__	42	SC	4210100	Mafra
__BRA__	42	SC	4210209	Major Gercino
__BRA__	42	SC	4210308	Major Vieira
__BRA__	42	SC	4210407	Maracajá
__BRA__	42	SC	4210506	Maravilha
__BRA__	42	SC	4210555	Marema
__BRA__	42	SC	4210605	Massaranduba
__BRA__	42	SC	4210704	Matos Costa
__BRA__	42	SC	4210803	Meleiro
__BRA__	42	SC	4210852	Mirim Doce
__BRA__	42	SC	4210902	Modelo
__BRA__	42	SC	4211009	Mondaí
__BRA__	42	SC	4211058	Monte Carlo
__BRA__	42	SC	4211108	Monte Castelo
__BRA__	42	SC	4211207	Morro da Fumaça
__BRA__	42	SC	4211256	Morro Grande
__BRA__	42	SC	4211306	Navegantes
__BRA__	42	SC	4211405	Nova Erechim
__BRA__	42	SC	4211454	Nova Itaberaba
__BRA__	42	SC	4211504	Nova Trento
__BRA__	42	SC	4211603	Nova Veneza
__BRA__	42	SC	4211652	Novo Horizonte
__BRA__	42	SC	4211702	Orleans
__BRA__	42	SC	4211751	Otacílio Costa
__BRA__	42	SC	4211801	Ouro
__BRA__	42	SC	4211850	Ouro Verde
__BRA__	42	SC	4211876	Paial
__BRA__	42	SC	4211892	Painel
__BRA__	42	SC	4211900	Palhoça
__BRA__	42	SC	4212007	Palma Sola
__BRA__	42	SC	4212056	Palmeira
__BRA__	42	SC	4212106	Palmitos
__BRA__	42	SC	4212205	Papanduva
__BRA__	42	SC	4212239	Paraíso
__BRA__	42	SC	4212254	Passo de Torres
__BRA__	42	SC	4212270	Passos Maia
__BRA__	42	SC	4212304	Paulo Lopes
__BRA__	42	SC	4212403	Pedras Grandes
__BRA__	42	SC	4212502	Penha
__BRA__	42	SC	4212601	Peritiba
__BRA__	42	SC	4212700	Petrolândia
__BRA__	42	SC	4212908	Pinhalzinho
__BRA__	42	SC	4213005	Pinheiro Preto
__BRA__	42	SC	4213104	Piratuba
__BRA__	42	SC	4213153	Planalto Alegre
__BRA__	42	SC	4213203	Pomerode
__BRA__	42	SC	4213302	Ponte Alta
__BRA__	42	SC	4213351	Ponte Alta do Norte
__BRA__	42	SC	4213401	Ponte Serrada
__BRA__	42	SC	4213500	Porto Belo
__BRA__	42	SC	4213609	Porto União
__BRA__	42	SC	4213708	Pouso Redondo
__BRA__	42	SC	4213807	Praia Grande
__BRA__	42	SC	4213906	Presidente Castello Branco
__BRA__	42	SC	4214003	Presidente Getúlio
__BRA__	42	SC	4214102	Presidente Nereu
__BRA__	42	SC	4214151	Princesa
__BRA__	42	SC	4214201	Quilombo
__BRA__	42	SC	4214300	Rancho Queimado
__BRA__	42	SC	4214409	Rio das Antas
__BRA__	42	SC	4214508	Rio do Campo
__BRA__	42	SC	4214607	Rio do Oeste
__BRA__	42	SC	4214805	Rio do Sul
__BRA__	42	SC	4214706	Rio dos Cedros
__BRA__	42	SC	4214904	Rio Fortuna
__BRA__	42	SC	4215000	Rio Negrinho
__BRA__	42	SC	4215059	Rio Rufino
__BRA__	42	SC	4215075	Riqueza
__BRA__	42	SC	4215109	Rodeio
__BRA__	42	SC	4215208	Romelândia
__BRA__	42	SC	4215307	Salete
__BRA__	42	SC	4215356	Saltinho
__BRA__	42	SC	4215406	Salto Veloso
__BRA__	42	SC	4215455	Sangão
__BRA__	42	SC	4215505	Santa Cecília
__BRA__	42	SC	4215554	Santa Helena
__BRA__	42	SC	4215604	Santa Rosa de Lima
__BRA__	42	SC	4215653	Santa Rosa do Sul
__BRA__	42	SC	4215679	Santa Terezinha
__BRA__	42	SC	4215687	Santa Terezinha do Progresso
__BRA__	42	SC	4215695	Santiago do Sul
__BRA__	42	SC	4215703	Santo Amaro da Imperatriz
__BRA__	42	SC	4215802	São Bento do Sul
__BRA__	42	SC	4215752	São Bernardino
__BRA__	42	SC	4215901	São Bonifácio
__BRA__	42	SC	4216008	São Carlos
__BRA__	42	SC	4216057	São Cristovão do Sul
__BRA__	42	SC	4216107	São Domingos
__BRA__	42	SC	4216206	São Francisco do Sul
__BRA__	42	SC	4216305	São João Batista
__BRA__	42	SC	4216354	São João do Itaperiú
__BRA__	42	SC	4216255	São João do Oeste
__BRA__	42	SC	4216404	São João do Sul
__BRA__	42	SC	4216503	São Joaquim
__BRA__	42	SC	4216602	São José
__BRA__	42	SC	4216701	São José do Cedro
__BRA__	42	SC	4216800	São José do Cerrito
__BRA__	42	SC	4216909	São Lourenço do Oeste
__BRA__	42	SC	4217006	São Ludgero
__BRA__	42	SC	4217105	São Martinho
__BRA__	42	SC	4217154	São Miguel da Boa Vista
__BRA__	42	SC	4217204	São Miguel do Oeste
__BRA__	42	SC	4217253	São Pedro de Alcântara
__BRA__	42	SC	4217303	Saudades
__BRA__	42	SC	4217402	Schroeder
__BRA__	42	SC	4217501	Seara
__BRA__	42	SC	4217550	Serra Alta
__BRA__	42	SC	4217600	Siderópolis
__BRA__	42	SC	4217709	Sombrio
__BRA__	42	SC	4217758	Sul Brasil
__BRA__	42	SC	4217808	Taió
__BRA__	42	SC	4217907	Tangará
__BRA__	42	SC	4217956	Tigrinhos
__BRA__	42	SC	4218004	Tijucas
__BRA__	42	SC	4218103	Timbé do Sul
__BRA__	42	SC	4218202	Timbó
__BRA__	42	SC	4218251	Timbó Grande
__BRA__	42	SC	4218301	Três Barras
__BRA__	42	SC	4218350	Treviso
__BRA__	42	SC	4218400	Treze de Maio
__BRA__	42	SC	4218509	Treze Tílias
__BRA__	42	SC	4218608	Trombudo Central
__BRA__	42	SC	4218707	Tubarão
__BRA__	42	SC	4218756	Tunápolis
__BRA__	42	SC	4218806	Turvo
__BRA__	42	SC	4218855	União do Oeste
__BRA__	42	SC	4218905	Urubici
__BRA__	42	SC	4218954	Urupema
__BRA__	42	SC	4219002	Urussanga
__BRA__	42	SC	4219101	Vargeão
__BRA__	42	SC	4219150	Vargem
__BRA__	42	SC	4219176	Vargem Bonita
__BRA__	42	SC	4219200	Vidal Ramos
__BRA__	42	SC	4219309	Videira
__BRA__	42	SC	4219358	Vitor Meireles
__BRA__	42	SC	4219408	Witmarsum
__BRA__	42	SC	4219507	Xanxerê
__BRA__	42	SC	4219606	Xavantina
__BRA__	42	SC	4219705	Xaxim
__BRA__	42	SC	4219853	Zortéa
__BRA__	41	PR	4100103	Abatiá
__BRA__	41	PR	4100202	Adrianópolis
__BRA__	41	PR	4100301	Agudos do Sul
__BRA__	41	PR	4100400	Almirante Tamandaré
__BRA__	41	PR	4100459	Altamira do Paraná
__BRA__	41	PR	4128625	Alto Paraíso
__BRA__	41	PR	4100608	Alto Paraná
__BRA__	41	PR	4100707	Alto Piquiri
__BRA__	41	PR	4100509	Altônia
__BRA__	41	PR	4100806	Alvorada do Sul
__BRA__	41	PR	4100905	Amaporã
__BRA__	41	PR	4101002	Ampére
__BRA__	41	PR	4101051	Anahy
__BRA__	41	PR	4101101	Andirá
__BRA__	41	PR	4101150	Ângulo
__BRA__	41	PR	4101200	Antonina
__BRA__	41	PR	4101309	Antônio Olinto
__BRA__	41	PR	4101408	Apucarana
__BRA__	41	PR	4101507	Arapongas
__BRA__	41	PR	4101606	Arapoti
__BRA__	41	PR	4101655	Arapuã
__BRA__	41	PR	4101705	Araruna
__BRA__	41	PR	4101804	Araucária
__BRA__	41	PR	4101853	Ariranha do Ivaí
__BRA__	41	PR	4101903	Assaí
__BRA__	41	PR	4102000	Assis Chateaubriand
__BRA__	41	PR	4102109	Astorga
__BRA__	41	PR	4102208	Atalaia
__BRA__	41	PR	4102307	Balsa Nova
__BRA__	41	PR	4102406	Bandeirantes
__BRA__	41	PR	4102505	Barbosa Ferraz
__BRA__	41	PR	4102703	Barra do Jacaré
__BRA__	41	PR	4102604	Barracão
__BRA__	41	PR	4102752	Bela Vista da Caroba
__BRA__	41	PR	4102802	Bela Vista do Paraíso
__BRA__	41	PR	4102901	Bituruna
__BRA__	41	PR	4103008	Boa Esperança
__BRA__	41	PR	4103024	Boa Esperança do Iguaçu
__BRA__	41	PR	4103040	Boa Ventura de São Roque
__BRA__	41	PR	4103057	Boa Vista da Aparecida
__BRA__	41	PR	4103107	Bocaiúva do Sul
__BRA__	41	PR	4103156	Bom Jesus do Sul
__BRA__	41	PR	4103206	Bom Sucesso
__BRA__	41	PR	4103222	Bom Sucesso do Sul
__BRA__	41	PR	4103305	Borrazópolis
__BRA__	41	PR	4103354	Braganey
__BRA__	41	PR	4103370	Brasilândia do Sul
__BRA__	41	PR	4103404	Cafeara
__BRA__	41	PR	4103453	Cafelândia
__BRA__	41	PR	4103479	Cafezal do Sul
__BRA__	41	PR	4103503	Califórnia
__BRA__	41	PR	4103602	Cambará
__BRA__	41	PR	4103701	Cambé
__BRA__	41	PR	4103800	Cambira
__BRA__	41	PR	4103909	Campina da Lagoa
__BRA__	41	PR	4103958	Campina do Simão
__BRA__	41	PR	4104006	Campina Grande do Sul
__BRA__	41	PR	4104055	Campo Bonito
__BRA__	41	PR	4104105	Campo do Tenente
__BRA__	41	PR	4104204	Campo Largo
__BRA__	41	PR	4104253	Campo Magro
__BRA__	41	PR	4104303	Campo Mourão
__BRA__	41	PR	4104402	Cândido de Abreu
__BRA__	41	PR	4104428	Candói
__BRA__	41	PR	4104451	Cantagalo
__BRA__	41	PR	4104501	Capanema
__BRA__	41	PR	4104600	Capitão Leônidas Marques
__BRA__	41	PR	4104659	Carambeí
__BRA__	41	PR	4104709	Carlópolis
__BRA__	41	PR	4104808	Cascavel
__BRA__	41	PR	4104907	Castro
__BRA__	41	PR	4105003	Catanduvas
__BRA__	41	PR	4105102	Centenário do Sul
__BRA__	41	PR	4105201	Cerro Azul
__BRA__	41	PR	4105300	Céu Azul
__BRA__	41	PR	4105409	Chopinzinho
__BRA__	41	PR	4105508	Cianorte
__BRA__	41	PR	4105607	Cidade Gaúcha
__BRA__	41	PR	4105706	Clevelândia
__BRA__	41	PR	4105805	Colombo
__BRA__	41	PR	4105904	Colorado
__BRA__	41	PR	4106001	Congonhinhas
__BRA__	41	PR	4106100	Conselheiro Mairinck
__BRA__	41	PR	4106209	Contenda
__BRA__	41	PR	4106308	Corbélia
__BRA__	41	PR	4106407	Cornélio Procópio
__BRA__	41	PR	4106456	Coronel Domingos Soares
__BRA__	41	PR	4106506	Coronel Vivida
__BRA__	41	PR	4106555	Corumbataí do Sul
__BRA__	41	PR	4106803	Cruz Machado
__BRA__	41	PR	4106571	Cruzeiro do Iguaçu
__BRA__	41	PR	4106605	Cruzeiro do Oeste
__BRA__	41	PR	4106704	Cruzeiro do Sul
__BRA__	41	PR	4106852	Cruzmaltina
__BRA__	41	PR	4106902	Curitiba
__BRA__	41	PR	4107009	Curiúva
__BRA__	41	PR	4107108	Diamante do Norte
__BRA__	41	PR	4107124	Diamante do Sul
__BRA__	41	PR	4107157	Diamante D'Oeste
__BRA__	41	PR	4107207	Dois Vizinhos
__BRA__	41	PR	4107256	Douradina
__BRA__	41	PR	4107306	Doutor Camargo
__BRA__	41	PR	4128633	Doutor Ulysses
__BRA__	41	PR	4107405	Enéas Marques
__BRA__	41	PR	4107504	Engenheiro Beltrão
__BRA__	41	PR	4107538	Entre Rios do Oeste
__BRA__	41	PR	4107520	Esperança Nova
__BRA__	41	PR	4107546	Espigão Alto do Iguaçu
__BRA__	41	PR	4107553	Farol
__BRA__	41	PR	4107603	Faxinal
__BRA__	41	PR	4107652	Fazenda Rio Grande
__BRA__	41	PR	4107702	Fênix
__BRA__	41	PR	4107736	Fernandes Pinheiro
__BRA__	41	PR	4107751	Figueira
__BRA__	41	PR	4107850	Flor da Serra do Sul
__BRA__	41	PR	4107801	Floraí
__BRA__	41	PR	4107900	Floresta
__BRA__	41	PR	4108007	Florestópolis
__BRA__	41	PR	4108106	Flórida
__BRA__	41	PR	4108205	Formosa do Oeste
__BRA__	41	PR	4108304	Foz do Iguaçu
__BRA__	41	PR	4108452	Foz do Jordão
__BRA__	41	PR	4108320	Francisco Alves
__BRA__	41	PR	4108403	Francisco Beltrão
__BRA__	41	PR	4108502	General Carneiro
__BRA__	41	PR	4108551	Godoy Moreira
__BRA__	41	PR	4108601	Goioerê
__BRA__	41	PR	4108650	Goioxim
__BRA__	41	PR	4108700	Grandes Rios
__BRA__	41	PR	4108809	Guaíra
__BRA__	41	PR	4108908	Guairaçá
__BRA__	41	PR	4108957	Guamiranga
__BRA__	41	PR	4109005	Guapirama
__BRA__	41	PR	4109104	Guaporema
__BRA__	41	PR	4109203	Guaraci
__BRA__	41	PR	4109302	Guaraniaçu
__BRA__	41	PR	4109401	Guarapuava
__BRA__	41	PR	4109500	Guaraqueçaba
__BRA__	41	PR	4109609	Guaratuba
__BRA__	41	PR	4109658	Honório Serpa
__BRA__	41	PR	4109708	Ibaiti
__BRA__	41	PR	4109757	Ibema
__BRA__	41	PR	4109807	Ibiporã
__BRA__	41	PR	4109906	Icaraíma
__BRA__	41	PR	4110003	Iguaraçu
__BRA__	41	PR	4110052	Iguatu
__BRA__	41	PR	4110078	Imbaú
__BRA__	41	PR	4110102	Imbituva
__BRA__	41	PR	4110201	Inácio Martins
__BRA__	41	PR	4110300	Inajá
__BRA__	41	PR	4110409	Indianópolis
__BRA__	41	PR	4110508	Ipiranga
__BRA__	41	PR	4110607	Iporã
__BRA__	41	PR	4110656	Iracema do Oeste
__BRA__	41	PR	4110706	Irati
__BRA__	41	PR	4110805	Iretama
__BRA__	41	PR	4110904	Itaguajé
__BRA__	41	PR	4110953	Itaipulândia
__BRA__	41	PR	4111001	Itambaracá
__BRA__	41	PR	4111100	Itambé
__BRA__	41	PR	4111209	Itapejara d'Oeste
__BRA__	41	PR	4111258	Itaperuçu
__BRA__	41	PR	4111308	Itaúna do Sul
__BRA__	41	PR	4111407	Ivaí
__BRA__	41	PR	4111506	Ivaiporã
__BRA__	41	PR	4111555	Ivaté
__BRA__	41	PR	4111605	Ivatuba
__BRA__	41	PR	4111704	Jaboti
__BRA__	41	PR	4111803	Jacarezinho
__BRA__	41	PR	4111902	Jaguapitã
__BRA__	41	PR	4112009	Jaguariaíva
__BRA__	41	PR	4112108	Jandaia do Sul
__BRA__	41	PR	4112207	Janiópolis
__BRA__	41	PR	4112306	Japira
__BRA__	41	PR	4112405	Japurá
__BRA__	41	PR	4112504	Jardim Alegre
__BRA__	41	PR	4112603	Jardim Olinda
__BRA__	41	PR	4112702	Jataizinho
__BRA__	41	PR	4112751	Jesuítas
__BRA__	41	PR	4112801	Joaquim Távora
__BRA__	41	PR	4112900	Jundiaí do Sul
__BRA__	41	PR	4112959	Juranda
__BRA__	41	PR	4113007	Jussara
__BRA__	41	PR	4113106	Kaloré
__BRA__	41	PR	4113205	Lapa
__BRA__	41	PR	4113254	Laranjal
__BRA__	41	PR	4113304	Laranjeiras do Sul
__BRA__	41	PR	4113403	Leópolis
__BRA__	41	PR	4113429	Lidianópolis
__BRA__	41	PR	4113452	Lindoeste
__BRA__	41	PR	4113502	Loanda
__BRA__	41	PR	4113601	Lobato
__BRA__	41	PR	4113700	Londrina
__BRA__	41	PR	4113734	Luiziana
__BRA__	41	PR	4113759	Lunardelli
__BRA__	41	PR	4113809	Lupionópolis
__BRA__	41	PR	4113908	Mallet
__BRA__	41	PR	4114005	Mamborê
__BRA__	41	PR	4114104	Mandaguaçu
__BRA__	41	PR	4114203	Mandaguari
__BRA__	41	PR	4114302	Mandirituba
__BRA__	41	PR	4114351	Manfrinópolis
__BRA__	41	PR	4114401	Mangueirinha
__BRA__	41	PR	4114500	Manoel Ribas
__BRA__	41	PR	4114609	Marechal Cândido Rondon
__BRA__	41	PR	4114708	Maria Helena
__BRA__	41	PR	4114807	Marialva
__BRA__	41	PR	4114906	Marilândia do Sul
__BRA__	41	PR	4115002	Marilena
__BRA__	41	PR	4115101	Mariluz
__BRA__	41	PR	4115200	Maringá
__BRA__	41	PR	4115309	Mariópolis
__BRA__	41	PR	4115358	Maripá
__BRA__	41	PR	4115408	Marmeleiro
__BRA__	41	PR	4115457	Marquinho
__BRA__	41	PR	4115507	Marumbi
__BRA__	41	PR	4115606	Matelândia
__BRA__	41	PR	4115705	Matinhos
__BRA__	41	PR	4115739	Mato Rico
__BRA__	41	PR	4115754	Mauá da Serra
__BRA__	41	PR	4115804	Medianeira
__BRA__	41	PR	4115853	Mercedes
__BRA__	41	PR	4115903	Mirador
__BRA__	41	PR	4116000	Miraselva
__BRA__	41	PR	4116059	Missal
__BRA__	41	PR	4116109	Moreira Sales
__BRA__	41	PR	4116208	Morretes
__BRA__	41	PR	4116307	Munhoz de Melo
__BRA__	41	PR	4116406	Nossa Senhora das Graças
__BRA__	41	PR	4116505	Nova Aliança do Ivaí
__BRA__	41	PR	4116604	Nova América da Colina
__BRA__	41	PR	4116703	Nova Aurora
__BRA__	41	PR	4116802	Nova Cantu
__BRA__	41	PR	4116901	Nova Esperança
__BRA__	41	PR	4116950	Nova Esperança do Sudoeste
__BRA__	41	PR	4117008	Nova Fátima
__BRA__	41	PR	4117057	Nova Laranjeiras
__BRA__	41	PR	4117107	Nova Londrina
__BRA__	41	PR	4117206	Nova Olímpia
__BRA__	41	PR	4117255	Nova Prata do Iguaçu
__BRA__	41	PR	4117214	Nova Santa Bárbara
__BRA__	41	PR	4117222	Nova Santa Rosa
__BRA__	41	PR	4117271	Nova Tebas
__BRA__	41	PR	4117297	Novo Itacolomi
__BRA__	41	PR	4117305	Ortigueira
__BRA__	41	PR	4117404	Ourizona
__BRA__	41	PR	4117453	Ouro Verde do Oeste
__BRA__	41	PR	4117503	Paiçandu
__BRA__	41	PR	4117602	Palmas
__BRA__	41	PR	4117701	Palmeira
__BRA__	41	PR	4117800	Palmital
__BRA__	41	PR	4117909	Palotina
__BRA__	41	PR	4118006	Paraíso do Norte
__BRA__	41	PR	4118105	Paranacity
__BRA__	41	PR	4118204	Paranaguá
__BRA__	41	PR	4118303	Paranapoema
__BRA__	41	PR	4118402	Paranavaí
__BRA__	41	PR	4118451	Pato Bragado
__BRA__	41	PR	4118501	Pato Branco
__BRA__	41	PR	4118600	Paula Freitas
__BRA__	41	PR	4118709	Paulo Frontin
__BRA__	41	PR	4118808	Peabiru
__BRA__	41	PR	4118857	Perobal
__BRA__	41	PR	4118907	Pérola
__BRA__	41	PR	4119004	Pérola d'Oeste
__BRA__	41	PR	4119103	Piên
__BRA__	41	PR	4119152	Pinhais
__BRA__	41	PR	4119251	Pinhal de São Bento
__BRA__	41	PR	4119202	Pinhalão
__BRA__	41	PR	4119301	Pinhão
__BRA__	41	PR	4119400	Piraí do Sul
__BRA__	41	PR	4119509	Piraquara
__BRA__	41	PR	4119608	Pitanga
__BRA__	41	PR	4119657	Pitangueiras
__BRA__	41	PR	4119707	Planaltina do Paraná
__BRA__	41	PR	4119806	Planalto
__BRA__	41	PR	4119905	Ponta Grossa
__BRA__	41	PR	4119954	Pontal do Paraná
__BRA__	41	PR	4120002	Porecatu
__BRA__	41	PR	4120101	Porto Amazonas
__BRA__	41	PR	4120150	Porto Barreiro
__BRA__	41	PR	4120200	Porto Rico
__BRA__	41	PR	4120309	Porto Vitória
__BRA__	41	PR	4120333	Prado Ferreira
__BRA__	41	PR	4120358	Pranchita
__BRA__	41	PR	4120408	Presidente Castelo Branco
__BRA__	41	PR	4120507	Primeiro de Maio
__BRA__	41	PR	4120606	Prudentópolis
__BRA__	41	PR	4120655	Quarto Centenário
__BRA__	41	PR	4120705	Quatiguá
__BRA__	41	PR	4120804	Quatro Barras
__BRA__	41	PR	4120853	Quatro Pontes
__BRA__	41	PR	4120903	Quedas do Iguaçu
__BRA__	41	PR	4121000	Querência do Norte
__BRA__	41	PR	4121109	Quinta do Sol
__BRA__	41	PR	4121208	Quitandinha
__BRA__	41	PR	4121257	Ramilândia
__BRA__	41	PR	4121307	Rancho Alegre
__BRA__	41	PR	4121356	Rancho Alegre D'Oeste
__BRA__	41	PR	4121406	Realeza
__BRA__	41	PR	4121505	Rebouças
__BRA__	41	PR	4121604	Renascença
__BRA__	41	PR	4121703	Reserva
__BRA__	41	PR	4121752	Reserva do Iguaçu
__BRA__	41	PR	4121802	Ribeirão Claro
__BRA__	41	PR	4121901	Ribeirão do Pinhal
__BRA__	41	PR	4122008	Rio Azul
__BRA__	41	PR	4122107	Rio Bom
__BRA__	41	PR	4122156	Rio Bonito do Iguaçu
__BRA__	41	PR	4122172	Rio Branco do Ivaí
__BRA__	41	PR	4122206	Rio Branco do Sul
__BRA__	41	PR	4122305	Rio Negro
__BRA__	41	PR	4122404	Rolândia
__BRA__	41	PR	4122503	Roncador
__BRA__	41	PR	4122602	Rondon
__BRA__	41	PR	4122651	Rosário do Ivaí
__BRA__	41	PR	4122701	Sabáudia
__BRA__	41	PR	4122800	Salgado Filho
__BRA__	41	PR	4122909	Salto do Itararé
__BRA__	41	PR	4123006	Salto do Lontra
__BRA__	41	PR	4123105	Santa Amélia
__BRA__	41	PR	4123204	Santa Cecília do Pavão
__BRA__	41	PR	4123303	Santa Cruz de Monte Castelo
__BRA__	41	PR	4123402	Santa Fé
__BRA__	41	PR	4123501	Santa Helena
__BRA__	41	PR	4123600	Santa Inês
__BRA__	41	PR	4123709	Santa Isabel do Ivaí
__BRA__	41	PR	4123808	Santa Izabel do Oeste
__BRA__	41	PR	4123824	Santa Lúcia
__BRA__	41	PR	4123857	Santa Maria do Oeste
__BRA__	41	PR	4123907	Santa Mariana
__BRA__	41	PR	4123956	Santa Mônica
__BRA__	41	PR	4124020	Santa Tereza do Oeste
__BRA__	41	PR	4124053	Santa Terezinha de Itaipu
__BRA__	41	PR	4124004	Santana do Itararé
__BRA__	41	PR	4124103	Santo Antônio da Platina
__BRA__	41	PR	4124202	Santo Antônio do Caiuá
__BRA__	41	PR	4124301	Santo Antônio do Paraíso
__BRA__	41	PR	4124400	Santo Antônio do Sudoeste
__BRA__	41	PR	4124509	Santo Inácio
__BRA__	41	PR	4124608	São Carlos do Ivaí
__BRA__	41	PR	4124707	São Jerônimo da Serra
__BRA__	41	PR	4124806	São João
__BRA__	41	PR	4124905	São João do Caiuá
__BRA__	41	PR	4125001	São João do Ivaí
__BRA__	41	PR	4125100	São João do Triunfo
__BRA__	41	PR	4125308	São Jorge do Ivaí
__BRA__	41	PR	4125357	São Jorge do Patrocínio
__BRA__	41	PR	4125209	São Jorge d'Oeste
__BRA__	41	PR	4125407	São José da Boa Vista
__BRA__	41	PR	4125456	São José das Palmeiras
__BRA__	41	PR	4125506	São José dos Pinhais
__BRA__	41	PR	4125555	São Manoel do Paraná
__BRA__	41	PR	4125605	São Mateus do Sul
__BRA__	41	PR	4125704	São Miguel do Iguaçu
__BRA__	41	PR	4125753	São Pedro do Iguaçu
__BRA__	41	PR	4125803	São Pedro do Ivaí
__BRA__	41	PR	4125902	São Pedro do Paraná
__BRA__	41	PR	4126009	São Sebastião da Amoreira
__BRA__	41	PR	4126108	São Tomé
__BRA__	41	PR	4126207	Sapopema
__BRA__	41	PR	4126256	Sarandi
__BRA__	41	PR	4126272	Saudade do Iguaçu
__BRA__	41	PR	4126306	Sengés
__BRA__	41	PR	4126355	Serranópolis do Iguaçu
__BRA__	41	PR	4126405	Sertaneja
__BRA__	41	PR	4126504	Sertanópolis
__BRA__	41	PR	4126603	Siqueira Campos
__BRA__	41	PR	4126652	Sulina
__BRA__	41	PR	4126678	Tamarana
__BRA__	41	PR	4126702	Tamboara
__BRA__	41	PR	4126801	Tapejara
__BRA__	41	PR	4126900	Tapira
__BRA__	41	PR	4127007	Teixeira Soares
__BRA__	41	PR	4127106	Telêmaco Borba
__BRA__	41	PR	4127205	Terra Boa
__BRA__	41	PR	4127304	Terra Rica
__BRA__	41	PR	4127403	Terra Roxa
__BRA__	41	PR	4127502	Tibagi
__BRA__	41	PR	4127601	Tijucas do Sul
__BRA__	41	PR	4127700	Toledo
__BRA__	41	PR	4127809	Tomazina
__BRA__	41	PR	4127858	Três Barras do Paraná
__BRA__	41	PR	4127882	Tunas do Paraná
__BRA__	41	PR	4127908	Tuneiras do Oeste
__BRA__	41	PR	4127957	Tupãssi
__BRA__	41	PR	4127965	Turvo
__BRA__	41	PR	4128005	Ubiratã
__BRA__	41	PR	4128104	Umuarama
__BRA__	41	PR	4128203	União da Vitória
__BRA__	41	PR	4128302	Uniflor
__BRA__	41	PR	4128401	Uraí
__BRA__	41	PR	4128534	Ventania
__BRA__	41	PR	4128559	Vera Cruz do Oeste
__BRA__	41	PR	4128609	Verê
__BRA__	41	PR	4128658	Virmond
__BRA__	41	PR	4128708	Vitorino
__BRA__	41	PR	4128500	Wenceslau Braz
__BRA__	41	PR	4128807	Xambrê
__BRA__	29	BA	2900108	Abaíra
__BRA__	29	BA	2900207	Abaré
__BRA__	29	BA	2900306	Acajutiba
__BRA__	29	BA	2900355	Adustina
__BRA__	29	BA	2900405	Água Fria
__BRA__	29	BA	2900603	Aiquara
__BRA__	29	BA	2900702	Alagoinhas
__BRA__	29	BA	2900801	Alcobaça
__BRA__	29	BA	2900900	Almadina
__BRA__	29	BA	2901007	Amargosa
__BRA__	29	BA	2901106	Amélia Rodrigues
__BRA__	29	BA	2901155	América Dourada
__BRA__	29	BA	2901205	Anagé
__BRA__	29	BA	2901304	Andaraí
__BRA__	29	BA	2901353	Andorinha
__BRA__	29	BA	2901403	Angical
__BRA__	29	BA	2901502	Anguera
__BRA__	29	BA	2901601	Antas
__BRA__	29	BA	2901700	Antônio Cardoso
__BRA__	29	BA	2901809	Antônio Gonçalves
__BRA__	29	BA	2901908	Aporá
__BRA__	29	BA	2901957	Apuarema
__BRA__	29	BA	2902054	Araças
__BRA__	29	BA	2902005	Aracatu
__BRA__	29	BA	2902104	Araci
__BRA__	29	BA	2902203	Aramari
__BRA__	29	BA	2902252	Arataca
__BRA__	29	BA	2902302	Aratuípe
__BRA__	29	BA	2902401	Aurelino Leal
__BRA__	29	BA	2902500	Baianópolis
__BRA__	29	BA	2902609	Baixa Grande
__BRA__	29	BA	2902658	Banzaê
__BRA__	29	BA	2902708	Barra
__BRA__	29	BA	2902807	Barra da Estiva
__BRA__	29	BA	2902906	Barra do Choça
__BRA__	29	BA	2903003	Barra do Mendes
__BRA__	29	BA	2903102	Barra do Rocha
__BRA__	29	BA	2903201	Barreiras
__BRA__	29	BA	2903235	Barro Alto
__BRA__	29	BA	2903300	Barro Preto
__BRA__	29	BA	2903276	Barrocas
__BRA__	29	BA	2903409	Belmonte
__BRA__	29	BA	2903508	Belo Campo
__BRA__	29	BA	2903607	Biritinga
__BRA__	29	BA	2903706	Boa Nova
__BRA__	29	BA	2903805	Boa Vista do Tupim
__BRA__	29	BA	2903904	Bom Jesus da Lapa
__BRA__	29	BA	2903953	Bom Jesus da Serra
__BRA__	29	BA	2904001	Boninal
__BRA__	29	BA	2904050	Bonito
__BRA__	29	BA	2904100	Boquira
__BRA__	29	BA	2904209	Botuporã
__BRA__	29	BA	2904308	Brejões
__BRA__	29	BA	2904407	Brejolândia
__BRA__	29	BA	2904506	Brotas de Macaúbas
__BRA__	29	BA	2904605	Brumado
__BRA__	29	BA	2904704	Buerarema
__BRA__	29	BA	2904753	Buritirama
__BRA__	29	BA	2904803	Caatiba
__BRA__	29	BA	2904852	Cabaceiras do Paraguaçu
__BRA__	29	BA	2904902	Cachoeira
__BRA__	29	BA	2905008	Caculé
__BRA__	29	BA	2905107	Caém
__BRA__	29	BA	2905156	Caetanos
__BRA__	29	BA	2905206	Caetité
__BRA__	29	BA	2905305	Cafarnaum
__BRA__	29	BA	2905404	Cairu
__BRA__	29	BA	2905503	Caldeirão Grande
__BRA__	29	BA	2905602	Camacan
__BRA__	29	BA	2905701	Camaçari
__BRA__	29	BA	2905800	Camamu
__BRA__	29	BA	2905909	Campo Alegre de Lourdes
__BRA__	29	BA	2906006	Campo Formoso
__BRA__	29	BA	2906105	Canápolis
__BRA__	29	BA	2906204	Canarana
__BRA__	29	BA	2906303	Canavieiras
__BRA__	29	BA	2906402	Candeal
__BRA__	29	BA	2906501	Candeias
__BRA__	29	BA	2906600	Candiba
__BRA__	29	BA	2906709	Cândido Sales
__BRA__	29	BA	2906808	Cansanção
__BRA__	29	BA	2906824	Canudos
__BRA__	29	BA	2906857	Capela do Alto Alegre
__BRA__	29	BA	2906873	Capim Grosso
__BRA__	29	BA	2906899	Caraíbas
__BRA__	29	BA	2906907	Caravelas
__BRA__	29	BA	2907004	Cardeal da Silva
__BRA__	29	BA	2907103	Carinhanha
__BRA__	29	BA	2907202	Casa Nova
__BRA__	29	BA	2907301	Castro Alves
__BRA__	29	BA	2907400	Catolândia
__BRA__	29	BA	2907509	Catu
__BRA__	29	BA	2907558	Caturama
__BRA__	29	BA	2907608	Central
__BRA__	29	BA	2907707	Chorrochó
__BRA__	29	BA	2907806	Cícero Dantas
__BRA__	29	BA	2907905	Cipó
__BRA__	29	BA	2908002	Coaraci
__BRA__	29	BA	2908101	Cocos
__BRA__	29	BA	2908200	Conceição da Feira
__BRA__	29	BA	2908309	Conceição do Almeida
__BRA__	29	BA	2908408	Conceição do Coité
__BRA__	29	BA	2908507	Conceição do Jacuípe
__BRA__	29	BA	2908606	Conde
__BRA__	29	BA	2908705	Condeúba
__BRA__	29	BA	2908804	Contendas do Sincorá
__BRA__	29	BA	2908903	Coração de Maria
__BRA__	29	BA	2909000	Cordeiros
__BRA__	29	BA	2909109	Coribe
__BRA__	29	BA	2909208	Coronel João Sá
__BRA__	29	BA	2909307	Correntina
__BRA__	29	BA	2909406	Cotegipe
__BRA__	29	BA	2909505	Cravolândia
__BRA__	29	BA	2909604	Crisópolis
__BRA__	29	BA	2909703	Cristópolis
__BRA__	29	BA	2909802	Cruz das Almas
__BRA__	29	BA	2909901	Curaçá
__BRA__	29	BA	2910008	Dário Meira
__BRA__	29	BA	2910057	Dias d'Ávila
__BRA__	29	BA	2910107	Dom Basílio
__BRA__	29	BA	2910206	Dom Macedo Costa
__BRA__	29	BA	2910305	Elísio Medrado
__BRA__	29	BA	2910404	Encruzilhada
__BRA__	29	BA	2910503	Entre Rios
__BRA__	29	BA	2900504	Érico Cardoso
__BRA__	29	BA	2910602	Esplanada
__BRA__	29	BA	2910701	Euclides da Cunha
__BRA__	29	BA	2910727	Eunápolis
__BRA__	29	BA	2910750	Fátima
__BRA__	29	BA	2910776	Feira da Mata
__BRA__	29	BA	2910800	Feira de Santana
__BRA__	29	BA	2910859	Filadélfia
__BRA__	29	BA	2910909	Firmino Alves
__BRA__	29	BA	2911006	Floresta Azul
__BRA__	29	BA	2911105	Formosa do Rio Preto
__BRA__	29	BA	2911204	Gandu
__BRA__	29	BA	2911253	Gavião
__BRA__	29	BA	2911303	Gentio do Ouro
__BRA__	29	BA	2911402	Glória
__BRA__	29	BA	2911501	Gongogi
__BRA__	29	BA	2911600	Governador Mangabeira
__BRA__	29	BA	2911659	Guajeru
__BRA__	29	BA	2911709	Guanambi
__BRA__	29	BA	2911808	Guaratinga
__BRA__	29	BA	2911857	Heliópolis
__BRA__	29	BA	2911907	Iaçu
__BRA__	29	BA	2912004	Ibiassucê
__BRA__	29	BA	2912103	Ibicaraí
__BRA__	29	BA	2912202	Ibicoara
__BRA__	29	BA	2912301	Ibicuí
__BRA__	29	BA	2912400	Ibipeba
__BRA__	29	BA	2912509	Ibipitanga
__BRA__	29	BA	2912608	Ibiquera
__BRA__	29	BA	2912707	Ibirapitanga
__BRA__	29	BA	2912806	Ibirapuã
__BRA__	29	BA	2912905	Ibirataia
__BRA__	29	BA	2913002	Ibitiara
__BRA__	29	BA	2913101	Ibititá
__BRA__	29	BA	2913200	Ibotirama
__BRA__	29	BA	2913309	Ichu
__BRA__	29	BA	2913408	Igaporã
__BRA__	29	BA	2913457	Igrapiúna
__BRA__	29	BA	2913507	Iguaí
__BRA__	29	BA	2913606	Ilhéus
__BRA__	29	BA	2913705	Inhambupe
__BRA__	29	BA	2913804	Ipecaetá
__BRA__	29	BA	2913903	Ipiaú
__BRA__	29	BA	2914000	Ipirá
__BRA__	29	BA	2914109	Ipupiara
__BRA__	29	BA	2914208	Irajuba
__BRA__	29	BA	2914307	Iramaia
__BRA__	29	BA	2914406	Iraquara
__BRA__	29	BA	2914505	Irará
__BRA__	29	BA	2914604	Irecê
__BRA__	29	BA	2914653	Itabela
__BRA__	29	BA	2914703	Itaberaba
__BRA__	29	BA	2914802	Itabuna
__BRA__	29	BA	2914901	Itacaré
__BRA__	29	BA	2915007	Itaeté
__BRA__	29	BA	2915106	Itagi
__BRA__	29	BA	2915205	Itagibá
__BRA__	29	BA	2915304	Itagimirim
__BRA__	29	BA	2915353	Itaguaçu da Bahia
__BRA__	29	BA	2915403	Itaju do Colônia
__BRA__	29	BA	2915502	Itajuípe
__BRA__	29	BA	2915601	Itamaraju
__BRA__	29	BA	2915700	Itamari
__BRA__	29	BA	2915809	Itambé
__BRA__	29	BA	2915908	Itanagra
__BRA__	29	BA	2916005	Itanhém
__BRA__	29	BA	2916104	Itaparica
__BRA__	29	BA	2916203	Itapé
__BRA__	29	BA	2916302	Itapebi
__BRA__	29	BA	2916401	Itapetinga
__BRA__	29	BA	2916500	Itapicuru
__BRA__	29	BA	2916609	Itapitanga
__BRA__	29	BA	2916708	Itaquara
__BRA__	29	BA	2916807	Itarantim
__BRA__	29	BA	2916856	Itatim
__BRA__	29	BA	2916906	Itiruçu
__BRA__	29	BA	2917003	Itiúba
__BRA__	29	BA	2917102	Itororó
__BRA__	29	BA	2917201	Ituaçu
__BRA__	29	BA	2917300	Ituberá
__BRA__	29	BA	2917334	Iuiú
__BRA__	29	BA	2917359	Jaborandi
__BRA__	29	BA	2917409	Jacaraci
__BRA__	29	BA	2917508	Jacobina
__BRA__	29	BA	2917607	Jaguaquara
__BRA__	29	BA	2917706	Jaguarari
__BRA__	29	BA	2917805	Jaguaripe
__BRA__	29	BA	2917904	Jandaíra
__BRA__	29	BA	2918001	Jequié
__BRA__	29	BA	2918100	Jeremoabo
__BRA__	29	BA	2918209	Jiquiriçá
__BRA__	29	BA	2918308	Jitaúna
__BRA__	29	BA	2918357	João Dourado
__BRA__	29	BA	2918407	Juazeiro
__BRA__	29	BA	2918456	Jucuruçu
__BRA__	29	BA	2918506	Jussara
__BRA__	29	BA	2918555	Jussari
__BRA__	29	BA	2918605	Jussiape
__BRA__	29	BA	2918704	Lafaiete Coutinho
__BRA__	29	BA	2918753	Lagoa Real
__BRA__	29	BA	2918803	Laje
__BRA__	29	BA	2918902	Lajedão
__BRA__	29	BA	2919009	Lajedinho
__BRA__	29	BA	2919058	Lajedo do Tabocal
__BRA__	29	BA	2919108	Lamarão
__BRA__	29	BA	2919157	Lapão
__BRA__	29	BA	2919207	Lauro de Freitas
__BRA__	29	BA	2919306	Lençóis
__BRA__	29	BA	2919405	Licínio de Almeida
__BRA__	29	BA	2919504	Livramento de Nossa Senhora
__BRA__	29	BA	2919553	Luís Eduardo Magalhães
__BRA__	29	BA	2919603	Macajuba
__BRA__	29	BA	2919702	Macarani
__BRA__	29	BA	2919801	Macaúbas
__BRA__	29	BA	2919900	Macururé
__BRA__	29	BA	2919926	Madre de Deus
__BRA__	29	BA	2919959	Maetinga
__BRA__	29	BA	2920007	Maiquinique
__BRA__	29	BA	2920106	Mairi
__BRA__	29	BA	2920205	Malhada
__BRA__	29	BA	2920304	Malhada de Pedras
__BRA__	29	BA	2920403	Manoel Vitorino
__BRA__	29	BA	2920452	Mansidão
__BRA__	29	BA	2920502	Maracás
__BRA__	29	BA	2920601	Maragogipe
__BRA__	29	BA	2920700	Maraú
__BRA__	29	BA	2920809	Marcionílio Souza
__BRA__	29	BA	2920908	Mascote
__BRA__	29	BA	2921005	Mata de São João
__BRA__	29	BA	2921054	Matina
__BRA__	29	BA	2921104	Medeiros Neto
__BRA__	29	BA	2921203	Miguel Calmon
__BRA__	29	BA	2921302	Milagres
__BRA__	29	BA	2921401	Mirangaba
__BRA__	29	BA	2921450	Mirante
__BRA__	29	BA	2921500	Monte Santo
__BRA__	29	BA	2921609	Morpará
__BRA__	29	BA	2921708	Morro do Chapéu
__BRA__	29	BA	2921807	Mortugaba
__BRA__	29	BA	2921906	Mucugê
__BRA__	29	BA	2922003	Mucuri
__BRA__	29	BA	2922052	Mulungu do Morro
__BRA__	29	BA	2922102	Mundo Novo
__BRA__	29	BA	2922201	Muniz Ferreira
__BRA__	29	BA	2922250	Muquém de São Francisco
__BRA__	29	BA	2922300	Muritiba
__BRA__	29	BA	2922409	Mutuípe
__BRA__	29	BA	2922508	Nazaré
__BRA__	29	BA	2922607	Nilo Peçanha
__BRA__	29	BA	2922656	Nordestina
__BRA__	29	BA	2922706	Nova Canaã
__BRA__	29	BA	2922730	Nova Fátima
__BRA__	29	BA	2922755	Nova Ibiá
__BRA__	29	BA	2922805	Nova Itarana
__BRA__	29	BA	2922854	Nova Redenção
__BRA__	29	BA	2922904	Nova Soure
__BRA__	29	BA	2923001	Nova Viçosa
__BRA__	29	BA	2923035	Novo Horizonte
__BRA__	29	BA	2923050	Novo Triunfo
__BRA__	29	BA	2923100	Olindina
__BRA__	29	BA	2923209	Oliveira dos Brejinhos
__BRA__	29	BA	2923308	Ouriçangas
__BRA__	29	BA	2923357	Ourolândia
__BRA__	29	BA	2923407	Palmas de Monte Alto
__BRA__	29	BA	2923506	Palmeiras
__BRA__	29	BA	2923605	Paramirim
__BRA__	29	BA	2923704	Paratinga
__BRA__	29	BA	2923803	Paripiranga
__BRA__	29	BA	2923902	Pau Brasil
__BRA__	29	BA	2924009	Paulo Afonso
__BRA__	29	BA	2924058	Pé de Serra
__BRA__	29	BA	2924108	Pedrão
__BRA__	29	BA	2924207	Pedro Alexandre
__BRA__	29	BA	2924306	Piatã
__BRA__	29	BA	2924405	Pilão Arcado
__BRA__	29	BA	2924504	Pindaí
__BRA__	29	BA	2924603	Pindobaçu
__BRA__	29	BA	2924652	Pintadas
__BRA__	29	BA	2924678	Piraí do Norte
__BRA__	29	BA	2924702	Piripá
__BRA__	29	BA	2924801	Piritiba
__BRA__	29	BA	2924900	Planaltino
__BRA__	29	BA	2925006	Planalto
__BRA__	29	BA	2925105	Poções
__BRA__	29	BA	2925204	Pojuca
__BRA__	29	BA	2925253	Ponto Novo
__BRA__	29	BA	2925303	Porto Seguro
__BRA__	29	BA	2925402	Potiraguá
__BRA__	29	BA	2925501	Prado
__BRA__	29	BA	2925600	Presidente Dutra
__BRA__	29	BA	2925709	Presidente Jânio Quadros
__BRA__	29	BA	2925758	Presidente Tancredo Neves
__BRA__	29	BA	2925808	Queimadas
__BRA__	29	BA	2925907	Quijingue
__BRA__	29	BA	2925931	Quixabeira
__BRA__	29	BA	2925956	Rafael Jambeiro
__BRA__	29	BA	2926004	Remanso
__BRA__	29	BA	2926103	Retirolândia
__BRA__	29	BA	2926202	Riachão das Neves
__BRA__	29	BA	2926301	Riachão do Jacuípe
__BRA__	29	BA	2926400	Riacho de Santana
__BRA__	29	BA	2926509	Ribeira do Amparo
__BRA__	29	BA	2926608	Ribeira do Pombal
__BRA__	29	BA	2926657	Ribeirão do Largo
__BRA__	29	BA	2926707	Rio de Contas
__BRA__	29	BA	2926806	Rio do Antônio
__BRA__	29	BA	2926905	Rio do Pires
__BRA__	29	BA	2927002	Rio Real
__BRA__	29	BA	2927101	Rodelas
__BRA__	29	BA	2927200	Ruy Barbosa
__BRA__	29	BA	2927309	Salinas da Margarida
__BRA__	29	BA	2927408	Salvador
__BRA__	29	BA	2927507	Santa Bárbara
__BRA__	29	BA	2927606	Santa Brígida
__BRA__	29	BA	2927705	Santa Cruz Cabrália
__BRA__	29	BA	2927804	Santa Cruz da Vitória
__BRA__	29	BA	2927903	Santa Inês
__BRA__	29	BA	2928059	Santa Luzia
__BRA__	29	BA	2928109	Santa Maria da Vitória
__BRA__	29	BA	2928406	Santa Rita de Cássia
__BRA__	29	BA	2928505	Santa Teresinha
__BRA__	29	BA	2928000	Santaluz
__BRA__	29	BA	2928208	Santana
__BRA__	29	BA	2928307	Santanópolis
__BRA__	29	BA	2928604	Santo Amaro
__BRA__	29	BA	2928703	Santo Antônio de Jesus
__BRA__	29	BA	2928802	Santo Estêvão
__BRA__	29	BA	2928901	São Desidério
__BRA__	29	BA	2928950	São Domingos
__BRA__	29	BA	2929107	São Felipe
__BRA__	29	BA	2929008	São Félix
__BRA__	29	BA	2929057	São Félix do Coribe
__BRA__	29	BA	2929206	São Francisco do Conde
__BRA__	29	BA	2929255	São Gabriel
__BRA__	29	BA	2929305	São Gonçalo dos Campos
__BRA__	29	BA	2929354	São José da Vitória
__BRA__	29	BA	2929370	São José do Jacuípe
__BRA__	29	BA	2929404	São Miguel das Matas
__BRA__	29	BA	2929503	São Sebastião do Passé
__BRA__	29	BA	2929602	Sapeaçu
__BRA__	29	BA	2929701	Sátiro Dias
__BRA__	29	BA	2929750	Saubara
__BRA__	29	BA	2929800	Saúde
__BRA__	29	BA	2929909	Seabra
__BRA__	29	BA	2930006	Sebastião Laranjeiras
__BRA__	29	BA	2930105	Senhor do Bonfim
__BRA__	29	BA	2930204	Sento Sé
__BRA__	29	BA	2930154	Serra do Ramalho
__BRA__	29	BA	2930303	Serra Dourada
__BRA__	29	BA	2930402	Serra Preta
__BRA__	29	BA	2930501	Serrinha
__BRA__	29	BA	2930600	Serrolândia
__BRA__	29	BA	2930709	Simões Filho
__BRA__	29	BA	2930758	Sítio do Mato
__BRA__	29	BA	2930766	Sítio do Quinto
__BRA__	29	BA	2930774	Sobradinho
__BRA__	29	BA	2930808	Souto Soares
__BRA__	29	BA	2930907	Tabocas do Brejo Velho
__BRA__	29	BA	2931004	Tanhaçu
__BRA__	29	BA	2931053	Tanque Novo
__BRA__	29	BA	2931103	Tanquinho
__BRA__	29	BA	2931202	Taperoá
__BRA__	29	BA	2931301	Tapiramutá
__BRA__	29	BA	2931350	Teixeira de Freitas
__BRA__	29	BA	2931400	Teodoro Sampaio
__BRA__	29	BA	2931509	Teofilândia
__BRA__	29	BA	2931608	Teolândia
__BRA__	29	BA	2931707	Terra Nova
__BRA__	29	BA	2931806	Tremedal
__BRA__	29	BA	2931905	Tucano
__BRA__	29	BA	2932002	Uauá
__BRA__	29	BA	2932101	Ubaíra
__BRA__	29	BA	2932200	Ubaitaba
__BRA__	29	BA	2932309	Ubatã
__BRA__	29	BA	2932408	Uibaí
__BRA__	29	BA	2932457	Umburanas
__BRA__	29	BA	2932507	Una
__BRA__	29	BA	2932606	Urandi
__BRA__	29	BA	2932705	Uruçuca
__BRA__	29	BA	2932804	Utinga
__BRA__	29	BA	2932903	Valença
__BRA__	29	BA	2933000	Valente
__BRA__	29	BA	2933059	Várzea da Roça
__BRA__	29	BA	2933109	Várzea do Poço
__BRA__	29	BA	2933158	Várzea Nova
__BRA__	29	BA	2933174	Varzedo
__BRA__	29	BA	2933208	Vera Cruz
__BRA__	29	BA	2933257	Vereda
__BRA__	29	BA	2933307	Vitória da Conquista
__BRA__	29	BA	2933406	Wagner
__BRA__	29	BA	2933455	Wanderley
__BRA__	29	BA	2933505	Wenceslau Guimarães
__BRA__	29	BA	2933604	Xique-Xique
__BRA__	43	RS	4300034	Aceguá
__BRA__	43	RS	4300059	Água Santa
__BRA__	43	RS	4300109	Agudo
__BRA__	43	RS	4300208	Ajuricaba
__BRA__	43	RS	4300307	Alecrim
__BRA__	43	RS	4300406	Alegrete
__BRA__	43	RS	4300455	Alegria
__BRA__	43	RS	4300471	Almirante Tamandaré do Sul
__BRA__	43	RS	4300505	Alpestre
__BRA__	43	RS	4300554	Alto Alegre
__BRA__	43	RS	4300570	Alto Feliz
__BRA__	43	RS	4300604	Alvorada
__BRA__	43	RS	4300638	Amaral Ferrador
__BRA__	43	RS	4300646	Ametista do Sul
__BRA__	43	RS	4300661	André da Rocha
__BRA__	43	RS	4300703	Anta Gorda
__BRA__	43	RS	4300802	Antônio Prado
__BRA__	43	RS	4300851	Arambaré
__BRA__	43	RS	4300877	Araricá
__BRA__	43	RS	4300901	Aratiba
__BRA__	43	RS	4301008	Arroio do Meio
__BRA__	43	RS	4301073	Arroio do Padre
__BRA__	43	RS	4301057	Arroio do Sal
__BRA__	43	RS	4301206	Arroio do Tigre
__BRA__	43	RS	4301107	Arroio dos Ratos
__BRA__	43	RS	4301305	Arroio Grande
__BRA__	43	RS	4301404	Arvorezinha
__BRA__	43	RS	4301503	Augusto Pestana
__BRA__	43	RS	4301552	Áurea
__BRA__	43	RS	4301602	Bagé
__BRA__	43	RS	4301636	Balneário Pinhal
__BRA__	43	RS	4301651	Barão
__BRA__	43	RS	4301701	Barão de Cotegipe
__BRA__	43	RS	4301750	Barão do Triunfo
__BRA__	43	RS	4301859	Barra do Guarita
__BRA__	43	RS	4301875	Barra do Quaraí
__BRA__	43	RS	4301909	Barra do Ribeiro
__BRA__	43	RS	4301925	Barra do Rio Azul
__BRA__	43	RS	4301958	Barra Funda
__BRA__	43	RS	4301800	Barracão
__BRA__	43	RS	4302006	Barros Cassal
__BRA__	43	RS	4302055	Benjamin Constant do Sul
__BRA__	43	RS	4302105	Bento Gonçalves
__BRA__	43	RS	4302154	Boa Vista das Missões
__BRA__	43	RS	4302204	Boa Vista do Buricá
__BRA__	43	RS	4302220	Boa Vista do Cadeado
__BRA__	43	RS	4302238	Boa Vista do Incra
__BRA__	43	RS	4302253	Boa Vista do Sul
__BRA__	43	RS	4302303	Bom Jesus
__BRA__	43	RS	4302352	Bom Princípio
__BRA__	43	RS	4302378	Bom Progresso
__BRA__	43	RS	4302402	Bom Retiro do Sul
__BRA__	43	RS	4302451	Boqueirão do Leão
__BRA__	43	RS	4302501	Bossoroca
__BRA__	43	RS	4302584	Bozano
__BRA__	43	RS	4302600	Braga
__BRA__	43	RS	4302659	Brochier
__BRA__	43	RS	4302709	Butiá
__BRA__	43	RS	4302808	Caçapava do Sul
__BRA__	43	RS	4302907	Cacequi
__BRA__	43	RS	4303004	Cachoeira do Sul
__BRA__	43	RS	4303103	Cachoeirinha
__BRA__	43	RS	4303202	Cacique Doble
__BRA__	43	RS	4303301	Caibaté
__BRA__	43	RS	4303400	Caiçara
__BRA__	43	RS	4303509	Camaquã
__BRA__	43	RS	4303558	Camargo
__BRA__	43	RS	4303608	Cambará do Sul
__BRA__	43	RS	4303673	Campestre da Serra
__BRA__	43	RS	4303707	Campina das Missões
__BRA__	43	RS	4303806	Campinas do Sul
__BRA__	43	RS	4303905	Campo Bom
__BRA__	43	RS	4304002	Campo Novo
__BRA__	43	RS	4304101	Campos Borges
__BRA__	43	RS	4304200	Candelária
__BRA__	43	RS	4304309	Cândido Godói
__BRA__	43	RS	4304358	Candiota
__BRA__	43	RS	4304408	Canela
__BRA__	43	RS	4304507	Canguçu
__BRA__	43	RS	4304606	Canoas
__BRA__	43	RS	4304614	Canudos do Vale
__BRA__	43	RS	4304622	Capão Bonito do Sul
__BRA__	43	RS	4304630	Capão da Canoa
__BRA__	43	RS	4304655	Capão do Cipó
__BRA__	43	RS	4304663	Capão do Leão
__BRA__	43	RS	4304689	Capela de Santana
__BRA__	43	RS	4304697	Capitão
__BRA__	43	RS	4304671	Capivari do Sul
__BRA__	43	RS	4304713	Caraá
__BRA__	43	RS	4304705	Carazinho
__BRA__	43	RS	4304804	Carlos Barbosa
__BRA__	43	RS	4304853	Carlos Gomes
__BRA__	43	RS	4304903	Casca
__BRA__	43	RS	4304952	Caseiros
__BRA__	43	RS	4305009	Catuípe
__BRA__	43	RS	4305108	Caxias do Sul
__BRA__	43	RS	4305116	Centenário
__BRA__	43	RS	4305124	Cerrito
__BRA__	43	RS	4305132	Cerro Branco
__BRA__	43	RS	4305157	Cerro Grande
__BRA__	43	RS	4305173	Cerro Grande do Sul
__BRA__	43	RS	4305207	Cerro Largo
__BRA__	43	RS	4305306	Chapada
__BRA__	43	RS	4305355	Charqueadas
__BRA__	43	RS	4305371	Charrua
__BRA__	43	RS	4305405	Chiapetta
__BRA__	43	RS	4305439	Chuí
__BRA__	43	RS	4305447	Chuvisca
__BRA__	43	RS	4305454	Cidreira
__BRA__	43	RS	4305504	Ciríaco
__BRA__	43	RS	4305587	Colinas
__BRA__	43	RS	4305603	Colorado
__BRA__	43	RS	4305702	Condor
__BRA__	43	RS	4305801	Constantina
__BRA__	43	RS	4305835	Coqueiro Baixo
__BRA__	43	RS	4305850	Coqueiros do Sul
__BRA__	43	RS	4305871	Coronel Barros
__BRA__	43	RS	4305900	Coronel Bicaco
__BRA__	43	RS	4305934	Coronel Pilar
__BRA__	43	RS	4305959	Cotiporã
__BRA__	43	RS	4305975	Coxilha
__BRA__	43	RS	4306007	Crissiumal
__BRA__	43	RS	4306056	Cristal
__BRA__	43	RS	4306072	Cristal do Sul
__BRA__	43	RS	4306106	Cruz Alta
__BRA__	43	RS	4306130	Cruzaltense
__BRA__	43	RS	4306205	Cruzeiro do Sul
__BRA__	43	RS	4306304	David Canabarro
__BRA__	43	RS	4306320	Derrubadas
__BRA__	43	RS	4306353	Dezesseis de Novembro
__BRA__	43	RS	4306379	Dilermando de Aguiar
__BRA__	43	RS	4306403	Dois Irmãos
__BRA__	43	RS	4306429	Dois Irmãos das Missões
__BRA__	43	RS	4306452	Dois Lajeados
__BRA__	43	RS	4306502	Dom Feliciano
__BRA__	43	RS	4306601	Dom Pedrito
__BRA__	43	RS	4306551	Dom Pedro de Alcântara
__BRA__	43	RS	4306700	Dona Francisca
__BRA__	43	RS	4306734	Doutor Maurício Cardoso
__BRA__	43	RS	4306759	Doutor Ricardo
__BRA__	43	RS	4306767	Eldorado do Sul
__BRA__	43	RS	4306809	Encantado
__BRA__	43	RS	4306908	Encruzilhada do Sul
__BRA__	43	RS	4306924	Engenho Velho
__BRA__	43	RS	4306957	Entre Rios do Sul
__BRA__	43	RS	4306932	Entre-Ijuís
__BRA__	43	RS	4306973	Erebango
__BRA__	43	RS	4307005	Erechim
__BRA__	43	RS	4307054	Ernestina
__BRA__	43	RS	4307203	Erval Grande
__BRA__	43	RS	4307302	Erval Seco
__BRA__	43	RS	4307401	Esmeralda
__BRA__	43	RS	4307450	Esperança do Sul
__BRA__	43	RS	4307500	Espumoso
__BRA__	43	RS	4307559	Estação
__BRA__	43	RS	4307609	Estância Velha
__BRA__	43	RS	4307708	Esteio
__BRA__	43	RS	4307807	Estrela
__BRA__	43	RS	4307815	Estrela Velha
__BRA__	43	RS	4307831	Eugênio de Castro
__BRA__	43	RS	4307864	Fagundes Varela
__BRA__	43	RS	4307906	Farroupilha
__BRA__	43	RS	4308003	Faxinal do Soturno
__BRA__	43	RS	4308052	Faxinalzinho
__BRA__	43	RS	4308078	Fazenda Vilanova
__BRA__	43	RS	4308102	Feliz
__BRA__	43	RS	4308201	Flores da Cunha
__BRA__	43	RS	4308250	Floriano Peixoto
__BRA__	43	RS	4308300	Fontoura Xavier
__BRA__	43	RS	4308409	Formigueiro
__BRA__	43	RS	4308433	Forquetinha
__BRA__	43	RS	4308458	Fortaleza dos Valos
__BRA__	43	RS	4308508	Frederico Westphalen
__BRA__	43	RS	4308607	Garibaldi
__BRA__	43	RS	4308656	Garruchos
__BRA__	43	RS	4308706	Gaurama
__BRA__	43	RS	4308805	General Câmara
__BRA__	43	RS	4308854	Gentil
__BRA__	43	RS	4308904	Getúlio Vargas
__BRA__	43	RS	4309001	Giruá
__BRA__	43	RS	4309050	Glorinha
__BRA__	43	RS	4309100	Gramado
__BRA__	43	RS	4309126	Gramado dos Loureiros
__BRA__	43	RS	4309159	Gramado Xavier
__BRA__	43	RS	4309209	Gravataí
__BRA__	43	RS	4309258	Guabiju
__BRA__	43	RS	4309308	Guaíba
__BRA__	43	RS	4309407	Guaporé
__BRA__	43	RS	4309506	Guarani das Missões
__BRA__	43	RS	4309555	Harmonia
__BRA__	43	RS	4307104	Herval
__BRA__	43	RS	4309571	Herveiras
__BRA__	43	RS	4309605	Horizontina
__BRA__	43	RS	4309654	Hulha Negra
__BRA__	43	RS	4309704	Humaitá
__BRA__	43	RS	4309753	Ibarama
__BRA__	43	RS	4309803	Ibiaçá
__BRA__	43	RS	4309902	Ibiraiaras
__BRA__	43	RS	4309951	Ibirapuitã
__BRA__	43	RS	4310009	Ibirubá
__BRA__	43	RS	4310108	Igrejinha
__BRA__	43	RS	4310207	Ijuí
__BRA__	43	RS	4310306	Ilópolis
__BRA__	43	RS	4310330	Imbé
__BRA__	43	RS	4310363	Imigrante
__BRA__	43	RS	4310405	Independência
__BRA__	43	RS	4310413	Inhacorá
__BRA__	43	RS	4310439	Ipê
__BRA__	43	RS	4310462	Ipiranga do Sul
__BRA__	43	RS	4310504	Iraí
__BRA__	43	RS	4310538	Itaara
__BRA__	43	RS	4310553	Itacurubi
__BRA__	43	RS	4310579	Itapuca
__BRA__	43	RS	4310603	Itaqui
__BRA__	43	RS	4310652	Itati
__BRA__	43	RS	4310702	Itatiba do Sul
__BRA__	43	RS	4310751	Ivorá
__BRA__	43	RS	4310801	Ivoti
__BRA__	43	RS	4310850	Jaboticaba
__BRA__	43	RS	4310876	Jacuizinho
__BRA__	43	RS	4310900	Jacutinga
__BRA__	43	RS	4311007	Jaguarão
__BRA__	43	RS	4311106	Jaguari
__BRA__	43	RS	4311122	Jaquirana
__BRA__	43	RS	4311130	Jari
__BRA__	43	RS	4311155	Jóia
__BRA__	43	RS	4311205	Júlio de Castilhos
__BRA__	43	RS	4311239	Lagoa Bonita do Sul
__BRA__	43	RS	4311270	Lagoa dos Três Cantos
__BRA__	43	RS	4311304	Lagoa Vermelha
__BRA__	43	RS	4311254	Lagoão
__BRA__	43	RS	4311403	Lajeado
__BRA__	43	RS	4311429	Lajeado do Bugre
__BRA__	43	RS	4311502	Lavras do Sul
__BRA__	43	RS	4311601	Liberato Salzano
__BRA__	43	RS	4311627	Lindolfo Collor
__BRA__	43	RS	4311643	Linha Nova
__BRA__	43	RS	4311718	Maçambara
__BRA__	43	RS	4311700	Machadinho
__BRA__	43	RS	4311734	Mampituba
__BRA__	43	RS	4311759	Manoel Viana
__BRA__	43	RS	4311775	Maquiné
__BRA__	43	RS	4311791	Maratá
__BRA__	43	RS	4311809	Marau
__BRA__	43	RS	4311908	Marcelino Ramos
__BRA__	43	RS	4311981	Mariana Pimentel
__BRA__	43	RS	4312005	Mariano Moro
__BRA__	43	RS	4312054	Marques de Souza
__BRA__	43	RS	4312104	Mata
__BRA__	43	RS	4312138	Mato Castelhano
__BRA__	43	RS	4312153	Mato Leitão
__BRA__	43	RS	4312179	Mato Queimado
__BRA__	43	RS	4312203	Maximiliano de Almeida
__BRA__	43	RS	4312252	Minas do Leão
__BRA__	43	RS	4312302	Miraguaí
__BRA__	43	RS	4312351	Montauri
__BRA__	43	RS	4312377	Monte Alegre dos Campos
__BRA__	43	RS	4312385	Monte Belo do Sul
__BRA__	43	RS	4312401	Montenegro
__BRA__	43	RS	4312427	Mormaço
__BRA__	43	RS	4312443	Morrinhos do Sul
__BRA__	43	RS	4312450	Morro Redondo
__BRA__	43	RS	4312476	Morro Reuter
__BRA__	43	RS	4312500	Mostardas
__BRA__	43	RS	4312609	Muçum
__BRA__	43	RS	4312617	Muitos Capões
__BRA__	43	RS	4312625	Muliterno
__BRA__	43	RS	4312658	Não-Me-Toque
__BRA__	43	RS	4312674	Nicolau Vergueiro
__BRA__	43	RS	4312708	Nonoai
__BRA__	43	RS	4312757	Nova Alvorada
__BRA__	43	RS	4312807	Nova Araçá
__BRA__	43	RS	4312906	Nova Bassano
__BRA__	43	RS	4312955	Nova Boa Vista
__BRA__	43	RS	4313003	Nova Bréscia
__BRA__	43	RS	4313011	Nova Candelária
__BRA__	43	RS	4313037	Nova Esperança do Sul
__BRA__	43	RS	4313060	Nova Hartz
__BRA__	43	RS	4313086	Nova Pádua
__BRA__	43	RS	4313102	Nova Palma
__BRA__	43	RS	4313201	Nova Petrópolis
__BRA__	43	RS	4313300	Nova Prata
__BRA__	43	RS	4313334	Nova Ramada
__BRA__	43	RS	4313359	Nova Roma do Sul
__BRA__	43	RS	4313375	Nova Santa Rita
__BRA__	43	RS	4313490	Novo Barreiro
__BRA__	43	RS	4313391	Novo Cabrais
__BRA__	43	RS	4313409	Novo Hamburgo
__BRA__	43	RS	4313425	Novo Machado
__BRA__	43	RS	4313441	Novo Tiradentes
__BRA__	43	RS	4313466	Novo Xingu
__BRA__	43	RS	4313508	Osório
__BRA__	43	RS	4313607	Paim Filho
__BRA__	43	RS	4313656	Palmares do Sul
__BRA__	43	RS	4313706	Palmeira das Missões
__BRA__	43	RS	4313805	Palmitinho
__BRA__	43	RS	4313904	Panambi
__BRA__	43	RS	4313953	Pantano Grande
__BRA__	43	RS	4314001	Paraí
__BRA__	43	RS	4314027	Paraíso do Sul
__BRA__	43	RS	4314035	Pareci Novo
__BRA__	43	RS	4314050	Parobé
__BRA__	43	RS	4314068	Passa Sete
__BRA__	43	RS	4314076	Passo do Sobrado
__BRA__	43	RS	4314100	Passo Fundo
__BRA__	43	RS	4314134	Paulo Bento
__BRA__	43	RS	4314159	Paverama
__BRA__	43	RS	4314175	Pedras Altas
__BRA__	43	RS	4314209	Pedro Osório
__BRA__	43	RS	4314308	Pejuçara
__BRA__	43	RS	4314407	Pelotas
__BRA__	43	RS	4314423	Picada Café
__BRA__	43	RS	4314456	Pinhal
__BRA__	43	RS	4314464	Pinhal da Serra
__BRA__	43	RS	4314472	Pinhal Grande
__BRA__	43	RS	4314498	Pinheirinho do Vale
__BRA__	43	RS	4314506	Pinheiro Machado
__BRA__	43	RS	4314555	Pirapó
__BRA__	43	RS	4314605	Piratini
__BRA__	43	RS	4314704	Planalto
__BRA__	43	RS	4314753	Poço das Antas
__BRA__	43	RS	4314779	Pontão
__BRA__	43	RS	4314787	Ponte Preta
__BRA__	43	RS	4314803	Portão
__BRA__	43	RS	4314902	Porto Alegre
__BRA__	43	RS	4315008	Porto Lucena
__BRA__	43	RS	4315057	Porto Mauá
__BRA__	43	RS	4315073	Porto Vera Cruz
__BRA__	43	RS	4315107	Porto Xavier
__BRA__	43	RS	4315131	Pouso Novo
__BRA__	43	RS	4315149	Presidente Lucena
__BRA__	43	RS	4315156	Progresso
__BRA__	43	RS	4315172	Protásio Alves
__BRA__	43	RS	4315206	Putinga
__BRA__	43	RS	4315305	Quaraí
__BRA__	43	RS	4315313	Quatro Irmãos
__BRA__	43	RS	4315321	Quevedos
__BRA__	43	RS	4315354	Quinze de Novembro
__BRA__	43	RS	4315404	Redentora
__BRA__	43	RS	4315453	Relvado
__BRA__	43	RS	4315503	Restinga Seca
__BRA__	43	RS	4315552	Rio dos Índios
__BRA__	43	RS	4315602	Rio Grande
__BRA__	43	RS	4315701	Rio Pardo
__BRA__	43	RS	4315750	Riozinho
__BRA__	43	RS	4315800	Roca Sales
__BRA__	43	RS	4315909	Rodeio Bonito
__BRA__	43	RS	4315958	Rolador
__BRA__	43	RS	4316006	Rolante
__BRA__	43	RS	4316105	Ronda Alta
__BRA__	43	RS	4316204	Rondinha
__BRA__	43	RS	4316303	Roque Gonzales
__BRA__	43	RS	4316402	Rosário do Sul
__BRA__	43	RS	4316428	Sagrada Família
__BRA__	43	RS	4316436	Saldanha Marinho
__BRA__	43	RS	4316451	Salto do Jacuí
__BRA__	43	RS	4316477	Salvador das Missões
__BRA__	43	RS	4316501	Salvador do Sul
__BRA__	43	RS	4316600	Sananduva
__BRA__	43	RS	4316709	Santa Bárbara do Sul
__BRA__	43	RS	4316733	Santa Cecília do Sul
__BRA__	43	RS	4316758	Santa Clara do Sul
__BRA__	43	RS	4316808	Santa Cruz do Sul
__BRA__	43	RS	4316972	Santa Margarida do Sul
__BRA__	43	RS	4316907	Santa Maria
__BRA__	43	RS	4316956	Santa Maria do Herval
__BRA__	43	RS	4317202	Santa Rosa
__BRA__	43	RS	4317251	Santa Tereza
__BRA__	43	RS	4317301	Santa Vitória do Palmar
__BRA__	43	RS	4317004	Santana da Boa Vista
__BRA__	43	RS	4317103	Santana do Livramento
__BRA__	43	RS	4317400	Santiago
__BRA__	43	RS	4317509	Santo Ângelo
__BRA__	43	RS	4317608	Santo Antônio da Patrulha
__BRA__	43	RS	4317707	Santo Antônio das Missões
__BRA__	43	RS	4317558	Santo Antônio do Palma
__BRA__	43	RS	4317756	Santo Antônio do Planalto
__BRA__	43	RS	4317806	Santo Augusto
__BRA__	43	RS	4317905	Santo Cristo
__BRA__	43	RS	4317954	Santo Expedito do Sul
__BRA__	43	RS	4318002	São Borja
__BRA__	43	RS	4318051	São Domingos do Sul
__BRA__	43	RS	4318101	São Francisco de Assis
__BRA__	43	RS	4318200	São Francisco de Paula
__BRA__	43	RS	4318309	São Gabriel
__BRA__	43	RS	4318408	São Jerônimo
__BRA__	43	RS	4318424	São João da Urtiga
__BRA__	43	RS	4318432	São João do Polêsine
__BRA__	43	RS	4318440	São Jorge
__BRA__	43	RS	4318457	São José das Missões
__BRA__	43	RS	4318465	São José do Herval
__BRA__	43	RS	4318481	São José do Hortêncio
__BRA__	43	RS	4318499	São José do Inhacorá
__BRA__	43	RS	4318507	São José do Norte
__BRA__	43	RS	4318606	São José do Ouro
__BRA__	43	RS	4318614	São José do Sul
__BRA__	43	RS	4318622	São José dos Ausentes
__BRA__	43	RS	4318705	São Leopoldo
__BRA__	43	RS	4318804	São Lourenço do Sul
__BRA__	43	RS	4318903	São Luiz Gonzaga
__BRA__	43	RS	4319000	São Marcos
__BRA__	43	RS	4319109	São Martinho
__BRA__	43	RS	4319125	São Martinho da Serra
__BRA__	43	RS	4319158	São Miguel das Missões
__BRA__	43	RS	4319208	São Nicolau
__BRA__	43	RS	4319307	São Paulo das Missões
__BRA__	43	RS	4319356	São Pedro da Serra
__BRA__	43	RS	4319364	São Pedro das Missões
__BRA__	43	RS	4319372	São Pedro do Butiá
__BRA__	43	RS	4319406	São Pedro do Sul
__BRA__	43	RS	4319505	São Sebastião do Caí
__BRA__	43	RS	4319604	São Sepé
__BRA__	43	RS	4319703	São Valentim
__BRA__	43	RS	4319711	São Valentim do Sul
__BRA__	43	RS	4319737	São Valério do Sul
__BRA__	43	RS	4319752	São Vendelino
__BRA__	43	RS	4319802	São Vicente do Sul
__BRA__	43	RS	4319901	Sapiranga
__BRA__	43	RS	4320008	Sapucaia do Sul
__BRA__	43	RS	4320107	Sarandi
__BRA__	43	RS	4320206	Seberi
__BRA__	43	RS	4320230	Sede Nova
__BRA__	43	RS	4320263	Segredo
__BRA__	43	RS	4320305	Selbach
__BRA__	43	RS	4320321	Senador Salgado Filho
__BRA__	43	RS	4320354	Sentinela do Sul
__BRA__	43	RS	4320404	Serafina Corrêa
__BRA__	43	RS	4320453	Sério
__BRA__	43	RS	4320503	Sertão
__BRA__	43	RS	4320552	Sertão Santana
__BRA__	43	RS	4320578	Sete de Setembro
__BRA__	43	RS	4320602	Severiano de Almeida
__BRA__	43	RS	4320651	Silveira Martins
__BRA__	43	RS	4320677	Sinimbu
__BRA__	43	RS	4320701	Sobradinho
__BRA__	43	RS	4320800	Soledade
__BRA__	43	RS	4320859	Tabaí
__BRA__	43	RS	4320909	Tapejara
__BRA__	43	RS	4321006	Tapera
__BRA__	43	RS	4321105	Tapes
__BRA__	43	RS	4321204	Taquara
__BRA__	43	RS	4321303	Taquari
__BRA__	43	RS	4321329	Taquaruçu do Sul
__BRA__	43	RS	4321352	Tavares
__BRA__	43	RS	4321402	Tenente Portela
__BRA__	43	RS	4321436	Terra de Areia
__BRA__	43	RS	4321451	Teutônia
__BRA__	43	RS	4321469	Tio Hugo
__BRA__	43	RS	4321477	Tiradentes do Sul
__BRA__	43	RS	4321493	Toropi
__BRA__	43	RS	4321501	Torres
__BRA__	43	RS	4321600	Tramandaí
__BRA__	43	RS	4321626	Travesseiro
__BRA__	43	RS	4321634	Três Arroios
__BRA__	43	RS	4321667	Três Cachoeiras
__BRA__	43	RS	4321709	Três Coroas
__BRA__	43	RS	4321808	Três de Maio
__BRA__	43	RS	4321832	Três Forquilhas
__BRA__	43	RS	4321857	Três Palmeiras
__BRA__	43	RS	4321907	Três Passos
__BRA__	43	RS	4321956	Trindade do Sul
__BRA__	43	RS	4322004	Triunfo
__BRA__	43	RS	4322103	Tucunduva
__BRA__	43	RS	4322152	Tunas
__BRA__	43	RS	4322186	Tupanci do Sul
__BRA__	43	RS	4322202	Tupanciretã
__BRA__	43	RS	4322251	Tupandi
__BRA__	43	RS	4322301	Tuparendi
__BRA__	43	RS	4322327	Turuçu
__BRA__	43	RS	4322343	Ubiretama
__BRA__	43	RS	4322350	União da Serra
__BRA__	43	RS	4322376	Unistalda
__BRA__	43	RS	4322400	Uruguaiana
__BRA__	43	RS	4322509	Vacaria
__BRA__	43	RS	4322533	Vale do Sol
__BRA__	43	RS	4322541	Vale Real
__BRA__	43	RS	4322525	Vale Verde
__BRA__	43	RS	4322558	Vanini
__BRA__	43	RS	4322608	Venâncio Aires
__BRA__	43	RS	4322707	Vera Cruz
__BRA__	43	RS	4322806	Veranópolis
__BRA__	43	RS	4322855	Vespasiano Correa
__BRA__	43	RS	4322905	Viadutos
__BRA__	43	RS	4323002	Viamão
__BRA__	43	RS	4323101	Vicente Dutra
__BRA__	43	RS	4323200	Victor Graeff
__BRA__	43	RS	4323309	Vila Flores
__BRA__	43	RS	4323358	Vila Lângaro
__BRA__	43	RS	4323408	Vila Maria
__BRA__	43	RS	4323457	Vila Nova do Sul
__BRA__	43	RS	4323507	Vista Alegre
__BRA__	43	RS	4323606	Vista Alegre do Prata
__BRA__	43	RS	4323705	Vista Gaúcha
__BRA__	43	RS	4323754	Vitória das Missões
__BRA__	43	RS	4323770	Westfalia
__BRA__	43	RS	4323804	Xangri-lá
__BRA__	35	SP	3500105	Adamantina
__BRA__	35	SP	3500204	Adolfo
__BRA__	35	SP	3500303	Aguaí
__BRA__	35	SP	3500402	Águas da Prata
__BRA__	35	SP	3500501	Águas de Lindóia
__BRA__	35	SP	3500550	Águas de Santa Bárbara
__BRA__	35	SP	3500600	Águas de São Pedro
__BRA__	35	SP	3500709	Agudos
__BRA__	35	SP	3500758	Alambari
__BRA__	35	SP	3500808	Alfredo Marcondes
__BRA__	35	SP	3500907	Altair
__BRA__	35	SP	3501004	Altinópolis
__BRA__	35	SP	3501103	Alto Alegre
__BRA__	35	SP	3501152	Alumínio
__BRA__	35	SP	3501202	Álvares Florence
__BRA__	35	SP	3501301	Álvares Machado
__BRA__	35	SP	3501400	Álvaro de Carvalho
__BRA__	35	SP	3501509	Alvinlândia
__BRA__	35	SP	3501608	Americana
__BRA__	35	SP	3501707	Américo Brasiliense
__BRA__	35	SP	3501806	Américo de Campos
__BRA__	35	SP	3501905	Amparo
__BRA__	35	SP	3502002	Analândia
__BRA__	35	SP	3502101	Andradina
__BRA__	35	SP	3502200	Angatuba
__BRA__	35	SP	3502309	Anhembi
__BRA__	35	SP	3502408	Anhumas
__BRA__	35	SP	3502507	Aparecida
__BRA__	35	SP	3502606	Aparecida d'Oeste
__BRA__	35	SP	3502705	Apiaí
__BRA__	35	SP	3502754	Araçariguama
__BRA__	35	SP	3502804	Araçatuba
__BRA__	35	SP	3502903	Araçoiaba da Serra
__BRA__	35	SP	3503000	Aramina
__BRA__	35	SP	3503109	Arandu
__BRA__	35	SP	3503158	Arapeí
__BRA__	35	SP	3503208	Araraquara
__BRA__	35	SP	3503307	Araras
__BRA__	35	SP	3503356	Arco-Íris
__BRA__	35	SP	3503406	Arealva
__BRA__	35	SP	3503505	Areias
__BRA__	35	SP	3503604	Areiópolis
__BRA__	35	SP	3503703	Ariranha
__BRA__	35	SP	3503802	Artur Nogueira
__BRA__	35	SP	3503901	Arujá
__BRA__	35	SP	3503950	Aspásia
__BRA__	35	SP	3504008	Assis
__BRA__	35	SP	3504107	Atibaia
__BRA__	35	SP	3504206	Auriflama
__BRA__	35	SP	3504305	Avaí
__BRA__	35	SP	3504404	Avanhandava
__BRA__	35	SP	3504503	Avaré
__BRA__	35	SP	3504602	Bady Bassitt
__BRA__	35	SP	3504701	Balbinos
__BRA__	35	SP	3504800	Bálsamo
__BRA__	35	SP	3504909	Bananal
__BRA__	35	SP	3505005	Barão de Antonina
__BRA__	35	SP	3505104	Barbosa
__BRA__	35	SP	3505203	Bariri
__BRA__	35	SP	3505302	Barra Bonita
__BRA__	35	SP	3505351	Barra do Chapéu
__BRA__	35	SP	3505401	Barra do Turvo
__BRA__	35	SP	3505500	Barretos
__BRA__	35	SP	3505609	Barrinha
__BRA__	35	SP	3505708	Barueri
__BRA__	35	SP	3505807	Bastos
__BRA__	35	SP	3505906	Batatais
__BRA__	35	SP	3506003	Bauru
__BRA__	35	SP	3506102	Bebedouro
__BRA__	35	SP	3506201	Bento de Abreu
__BRA__	35	SP	3506300	Bernardino de Campos
__BRA__	35	SP	3506359	Bertioga
__BRA__	35	SP	3506409	Bilac
__BRA__	35	SP	3506508	Birigui
__BRA__	35	SP	3506607	Biritiba-Mirim
__BRA__	35	SP	3506706	Boa Esperança do Sul
__BRA__	35	SP	3506805	Bocaina
__BRA__	35	SP	3506904	Bofete
__BRA__	35	SP	3507001	Boituva
__BRA__	35	SP	3507100	Bom Jesus dos Perdões
__BRA__	35	SP	3507159	Bom Sucesso de Itararé
__BRA__	35	SP	3507209	Borá
__BRA__	35	SP	3507308	Boracéia
__BRA__	35	SP	3507407	Borborema
__BRA__	35	SP	3507456	Borebi
__BRA__	35	SP	3507506	Botucatu
__BRA__	35	SP	3507605	Bragança Paulista
__BRA__	35	SP	3507704	Braúna
__BRA__	35	SP	3507753	Brejo Alegre
__BRA__	35	SP	3507803	Brodowski
__BRA__	35	SP	3507902	Brotas
__BRA__	35	SP	3508009	Buri
__BRA__	35	SP	3508108	Buritama
__BRA__	35	SP	3508207	Buritizal
__BRA__	35	SP	3508306	Cabrália Paulista
__BRA__	35	SP	3508405	Cabreúva
__BRA__	35	SP	3508504	Caçapava
__BRA__	35	SP	3508603	Cachoeira Paulista
__BRA__	35	SP	3508702	Caconde
__BRA__	35	SP	3508801	Cafelândia
__BRA__	35	SP	3508900	Caiabu
__BRA__	35	SP	3509007	Caieiras
__BRA__	35	SP	3509106	Caiuá
__BRA__	35	SP	3509205	Cajamar
__BRA__	35	SP	3509254	Cajati
__BRA__	35	SP	3509304	Cajobi
__BRA__	35	SP	3509403	Cajuru
__BRA__	35	SP	3509452	Campina do Monte Alegre
__BRA__	35	SP	3509502	Campinas
__BRA__	35	SP	3509601	Campo Limpo Paulista
__BRA__	35	SP	3509700	Campos do Jordão
__BRA__	35	SP	3509809	Campos Novos Paulista
__BRA__	35	SP	3509908	Cananéia
__BRA__	35	SP	3509957	Canas
__BRA__	35	SP	3510005	Cândido Mota
__BRA__	35	SP	3510104	Cândido Rodrigues
__BRA__	35	SP	3510153	Canitar
__BRA__	35	SP	3510203	Capão Bonito
__BRA__	35	SP	3510302	Capela do Alto
__BRA__	35	SP	3510401	Capivari
__BRA__	35	SP	3510500	Caraguatatuba
__BRA__	35	SP	3510609	Carapicuíba
__BRA__	35	SP	3510708	Cardoso
__BRA__	35	SP	3510807	Casa Branca
__BRA__	35	SP	3510906	Cássia dos Coqueiros
__BRA__	35	SP	3511003	Castilho
__BRA__	35	SP	3511102	Catanduva
__BRA__	35	SP	3511201	Catiguá
__BRA__	35	SP	3511300	Cedral
__BRA__	35	SP	3511409	Cerqueira César
__BRA__	35	SP	3511508	Cerquilho
__BRA__	35	SP	3511607	Cesário Lange
__BRA__	35	SP	3511706	Charqueada
__BRA__	35	SP	3557204	Chavantes
__BRA__	35	SP	3511904	Clementina
__BRA__	35	SP	3512001	Colina
__BRA__	35	SP	3512100	Colômbia
__BRA__	35	SP	3512209	Conchal
__BRA__	35	SP	3512308	Conchas
__BRA__	35	SP	3512407	Cordeirópolis
__BRA__	35	SP	3512506	Coroados
__BRA__	35	SP	3512605	Coronel Macedo
__BRA__	35	SP	3512704	Corumbataí
__BRA__	35	SP	3512803	Cosmópolis
__BRA__	35	SP	3512902	Cosmorama
__BRA__	35	SP	3513009	Cotia
__BRA__	35	SP	3513108	Cravinhos
__BRA__	35	SP	3513207	Cristais Paulista
__BRA__	35	SP	3513306	Cruzália
__BRA__	35	SP	3513405	Cruzeiro
__BRA__	35	SP	3513504	Cubatão
__BRA__	35	SP	3513603	Cunha
__BRA__	35	SP	3513702	Descalvado
__BRA__	35	SP	3513801	Diadema
__BRA__	35	SP	3513850	Dirce Reis
__BRA__	35	SP	3513900	Divinolândia
__BRA__	35	SP	3514007	Dobrada
__BRA__	35	SP	3514106	Dois Córregos
__BRA__	35	SP	3514205	Dolcinópolis
__BRA__	35	SP	3514304	Dourado
__BRA__	35	SP	3514403	Dracena
__BRA__	35	SP	3514502	Duartina
__BRA__	35	SP	3514601	Dumont
__BRA__	35	SP	3514700	Echaporã
__BRA__	35	SP	3514809	Eldorado
__BRA__	35	SP	3514908	Elias Fausto
__BRA__	35	SP	3514924	Elisiário
__BRA__	35	SP	3514957	Embaúba
__BRA__	35	SP	3515004	Embu
__BRA__	35	SP	3515103	Embu-Guaçu
__BRA__	35	SP	3515129	Emilianópolis
__BRA__	35	SP	3515152	Engenheiro Coelho
__BRA__	35	SP	3515186	Espírito Santo do Pinhal
__BRA__	35	SP	3515194	Espírito Santo do Turvo
__BRA__	35	SP	3557303	Estiva Gerbi
__BRA__	35	SP	3515301	Estrela do Norte
__BRA__	35	SP	3515202	Estrela d'Oeste
__BRA__	35	SP	3515350	Euclides da Cunha Paulista
__BRA__	35	SP	3515400	Fartura
__BRA__	35	SP	3515608	Fernando Prestes
__BRA__	35	SP	3515509	Fernandópolis
__BRA__	35	SP	3515657	Fernão
__BRA__	35	SP	3515707	Ferraz de Vasconcelos
__BRA__	35	SP	3515806	Flora Rica
__BRA__	35	SP	3515905	Floreal
__BRA__	35	SP	3516002	Flórida Paulista
__BRA__	35	SP	3516101	Florínia
__BRA__	35	SP	3516200	Franca
__BRA__	35	SP	3516309	Francisco Morato
__BRA__	35	SP	3516408	Franco da Rocha
__BRA__	35	SP	3516507	Gabriel Monteiro
__BRA__	35	SP	3516606	Gália
__BRA__	35	SP	3516705	Garça
__BRA__	35	SP	3516804	Gastão Vidigal
__BRA__	35	SP	3516853	Gavião Peixoto
__BRA__	35	SP	3516903	General Salgado
__BRA__	35	SP	3517000	Getulina
__BRA__	35	SP	3517109	Glicério
__BRA__	35	SP	3517208	Guaiçara
__BRA__	35	SP	3517307	Guaimbê
__BRA__	35	SP	3517406	Guaíra
__BRA__	35	SP	3517505	Guapiaçu
__BRA__	35	SP	3517604	Guapiara
__BRA__	35	SP	3517703	Guará
__BRA__	35	SP	3517802	Guaraçaí
__BRA__	35	SP	3517901	Guaraci
__BRA__	35	SP	3518008	Guarani d'Oeste
__BRA__	35	SP	3518107	Guarantã
__BRA__	35	SP	3518206	Guararapes
__BRA__	35	SP	3518305	Guararema
__BRA__	35	SP	3518404	Guaratinguetá
__BRA__	35	SP	3518503	Guareí
__BRA__	35	SP	3518602	Guariba
__BRA__	35	SP	3518701	Guarujá
__BRA__	35	SP	3518800	Guarulhos
__BRA__	35	SP	3518859	Guatapará
__BRA__	35	SP	3518909	Guzolândia
__BRA__	35	SP	3519006	Herculândia
__BRA__	35	SP	3519055	Holambra
__BRA__	35	SP	3519071	Hortolândia
__BRA__	35	SP	3519105	Iacanga
__BRA__	35	SP	3519204	Iacri
__BRA__	35	SP	3519253	Iaras
__BRA__	35	SP	3519303	Ibaté
__BRA__	35	SP	3519402	Ibirá
__BRA__	35	SP	3519501	Ibirarema
__BRA__	35	SP	3519600	Ibitinga
__BRA__	35	SP	3519709	Ibiúna
__BRA__	35	SP	3519808	Icém
__BRA__	35	SP	3519907	Iepê
__BRA__	35	SP	3520004	Igaraçu do Tietê
__BRA__	35	SP	3520103	Igarapava
__BRA__	35	SP	3520202	Igaratá
__BRA__	35	SP	3520301	Iguape
__BRA__	35	SP	3520426	Ilha Comprida
__BRA__	35	SP	3520442	Ilha Solteira
__BRA__	35	SP	3520400	Ilhabela
__BRA__	35	SP	3520509	Indaiatuba
__BRA__	35	SP	3520608	Indiana
__BRA__	35	SP	3520707	Indiaporã
__BRA__	35	SP	3520806	Inúbia Paulista
__BRA__	35	SP	3520905	Ipaussu
__BRA__	35	SP	3521002	Iperó
__BRA__	35	SP	3521101	Ipeúna
__BRA__	35	SP	3521150	Ipiguá
__BRA__	35	SP	3521200	Iporanga
__BRA__	35	SP	3521309	Ipuã
__BRA__	35	SP	3521408	Iracemápolis
__BRA__	35	SP	3521507	Irapuã
__BRA__	35	SP	3521606	Irapuru
__BRA__	35	SP	3521705	Itaberá
__BRA__	35	SP	3521804	Itaí
__BRA__	35	SP	3521903	Itajobi
__BRA__	35	SP	3522000	Itaju
__BRA__	35	SP	3522109	Itanhaém
__BRA__	35	SP	3522158	Itaóca
__BRA__	35	SP	3522208	Itapecerica da Serra
__BRA__	35	SP	3522307	Itapetininga
__BRA__	35	SP	3522406	Itapeva
__BRA__	35	SP	3522505	Itapevi
__BRA__	35	SP	3522604	Itapira
__BRA__	35	SP	3522653	Itapirapuã Paulista
__BRA__	35	SP	3522703	Itápolis
__BRA__	35	SP	3522802	Itaporanga
__BRA__	35	SP	3522901	Itapuí
__BRA__	35	SP	3523008	Itapura
__BRA__	35	SP	3523107	Itaquaquecetuba
__BRA__	35	SP	3523206	Itararé
__BRA__	35	SP	3523305	Itariri
__BRA__	35	SP	3523404	Itatiba
__BRA__	35	SP	3523503	Itatinga
__BRA__	35	SP	3523602	Itirapina
__BRA__	35	SP	3523701	Itirapuã
__BRA__	35	SP	3523800	Itobi
__BRA__	35	SP	3523909	Itu
__BRA__	35	SP	3524006	Itupeva
__BRA__	35	SP	3524105	Ituverava
__BRA__	35	SP	3524204	Jaborandi
__BRA__	35	SP	3524303	Jaboticabal
__BRA__	35	SP	3524402	Jacareí
__BRA__	35	SP	3524501	Jaci
__BRA__	35	SP	3524600	Jacupiranga
__BRA__	35	SP	3524709	Jaguariúna
__BRA__	35	SP	3524808	Jales
__BRA__	35	SP	3524907	Jambeiro
__BRA__	35	SP	3525003	Jandira
__BRA__	35	SP	3525102	Jardinópolis
__BRA__	35	SP	3525201	Jarinu
__BRA__	35	SP	3525300	Jaú
__BRA__	35	SP	3525409	Jeriquara
__BRA__	35	SP	3525508	Joanópolis
__BRA__	35	SP	3525607	João Ramalho
__BRA__	35	SP	3525706	José Bonifácio
__BRA__	35	SP	3525805	Júlio Mesquita
__BRA__	35	SP	3525854	Jumirim
__BRA__	35	SP	3525904	Jundiaí
__BRA__	35	SP	3526001	Junqueirópolis
__BRA__	35	SP	3526100	Juquiá
__BRA__	35	SP	3526209	Juquitiba
__BRA__	35	SP	3526308	Lagoinha
__BRA__	35	SP	3526407	Laranjal Paulista
__BRA__	35	SP	3526506	Lavínia
__BRA__	35	SP	3526605	Lavrinhas
__BRA__	35	SP	3526704	Leme
__BRA__	35	SP	3526803	Lençóis Paulista
__BRA__	35	SP	3526902	Limeira
__BRA__	35	SP	3527009	Lindóia
__BRA__	35	SP	3527108	Lins
__BRA__	35	SP	3527207	Lorena
__BRA__	35	SP	3527256	Lourdes
__BRA__	35	SP	3527306	Louveira
__BRA__	35	SP	3527405	Lucélia
__BRA__	35	SP	3527504	Lucianópolis
__BRA__	35	SP	3527603	Luís Antônio
__BRA__	35	SP	3527702	Luiziânia
__BRA__	35	SP	3527801	Lupércio
__BRA__	35	SP	3527900	Lutécia
__BRA__	35	SP	3528007	Macatuba
__BRA__	35	SP	3528106	Macaubal
__BRA__	35	SP	3528205	Macedônia
__BRA__	35	SP	3528304	Magda
__BRA__	35	SP	3528403	Mairinque
__BRA__	35	SP	3528502	Mairiporã
__BRA__	35	SP	3528601	Manduri
__BRA__	35	SP	3528700	Marabá Paulista
__BRA__	35	SP	3528809	Maracaí
__BRA__	35	SP	3528858	Marapoama
__BRA__	35	SP	3528908	Mariápolis
__BRA__	35	SP	3529005	Marília
__BRA__	35	SP	3529104	Marinópolis
__BRA__	35	SP	3529203	Martinópolis
__BRA__	35	SP	3529302	Matão
__BRA__	35	SP	3529401	Mauá
__BRA__	35	SP	3529500	Mendonça
__BRA__	35	SP	3529609	Meridiano
__BRA__	35	SP	3529658	Mesópolis
__BRA__	35	SP	3529708	Miguelópolis
__BRA__	35	SP	3529807	Mineiros do Tietê
__BRA__	35	SP	3530003	Mira Estrela
__BRA__	35	SP	3529906	Miracatu
__BRA__	35	SP	3530102	Mirandópolis
__BRA__	35	SP	3530201	Mirante do Paranapanema
__BRA__	35	SP	3530300	Mirassol
__BRA__	35	SP	3530409	Mirassolândia
__BRA__	35	SP	3530508	Mococa
__BRA__	35	SP	3530607	Mogi das Cruzes
__BRA__	35	SP	3530706	Mogi Guaçu
__BRA__	35	SP	3530805	Moji Mirim
__BRA__	35	SP	3530904	Mombuca
__BRA__	35	SP	3531001	Monções
__BRA__	35	SP	3531100	Mongaguá
__BRA__	35	SP	3531209	Monte Alegre do Sul
__BRA__	35	SP	3531308	Monte Alto
__BRA__	35	SP	3531407	Monte Aprazível
__BRA__	35	SP	3531506	Monte Azul Paulista
__BRA__	35	SP	3531605	Monte Castelo
__BRA__	35	SP	3531803	Monte Mor
__BRA__	35	SP	3531704	Monteiro Lobato
__BRA__	35	SP	3531902	Morro Agudo
__BRA__	35	SP	3532009	Morungaba
__BRA__	35	SP	3532058	Motuca
__BRA__	35	SP	3532108	Murutinga do Sul
__BRA__	35	SP	3532157	Nantes
__BRA__	35	SP	3532207	Narandiba
__BRA__	35	SP	3532306	Natividade da Serra
__BRA__	35	SP	3532405	Nazaré Paulista
__BRA__	35	SP	3532504	Neves Paulista
__BRA__	35	SP	3532603	Nhandeara
__BRA__	35	SP	3532702	Nipoã
__BRA__	35	SP	3532801	Nova Aliança
__BRA__	35	SP	3532827	Nova Campina
__BRA__	35	SP	3532843	Nova Canaã Paulista
__BRA__	35	SP	3532868	Nova Castilho
__BRA__	35	SP	3532900	Nova Europa
__BRA__	35	SP	3533007	Nova Granada
__BRA__	35	SP	3533106	Nova Guataporanga
__BRA__	35	SP	3533205	Nova Independência
__BRA__	35	SP	3533304	Nova Luzitânia
__BRA__	35	SP	3533403	Nova Odessa
__BRA__	35	SP	3533254	Novais
__BRA__	35	SP	3533502	Novo Horizonte
__BRA__	35	SP	3533601	Nuporanga
__BRA__	35	SP	3533700	Ocauçu
__BRA__	35	SP	3533809	Óleo
__BRA__	35	SP	3533908	Olímpia
__BRA__	35	SP	3534005	Onda Verde
__BRA__	35	SP	3534104	Oriente
__BRA__	35	SP	3534203	Orindiúva
__BRA__	35	SP	3534302	Orlândia
__BRA__	35	SP	3534401	Osasco
__BRA__	35	SP	3534500	Oscar Bressane
__BRA__	35	SP	3534609	Osvaldo Cruz
__BRA__	35	SP	3534708	Ourinhos
__BRA__	35	SP	3534807	Ouro Verde
__BRA__	35	SP	3534757	Ouroeste
__BRA__	35	SP	3534906	Pacaembu
__BRA__	35	SP	3535002	Palestina
__BRA__	35	SP	3535101	Palmares Paulista
__BRA__	35	SP	3535200	Palmeira d'Oeste
__BRA__	35	SP	3535309	Palmital
__BRA__	35	SP	3535408	Panorama
__BRA__	35	SP	3535507	Paraguaçu Paulista
__BRA__	35	SP	3535606	Paraibuna
__BRA__	35	SP	3535705	Paraíso
__BRA__	35	SP	3535804	Paranapanema
__BRA__	35	SP	3535903	Paranapuã
__BRA__	35	SP	3536000	Parapuã
__BRA__	35	SP	3536109	Pardinho
__BRA__	35	SP	3536208	Pariquera-Açu
__BRA__	35	SP	3536257	Parisi
__BRA__	35	SP	3536307	Patrocínio Paulista
__BRA__	35	SP	3536406	Paulicéia
__BRA__	35	SP	3536505	Paulínia
__BRA__	35	SP	3536570	Paulistânia
__BRA__	35	SP	3536604	Paulo de Faria
__BRA__	35	SP	3536703	Pederneiras
__BRA__	35	SP	3536802	Pedra Bela
__BRA__	35	SP	3536901	Pedranópolis
__BRA__	35	SP	3537008	Pedregulho
__BRA__	35	SP	3537107	Pedreira
__BRA__	35	SP	3537156	Pedrinhas Paulista
__BRA__	35	SP	3537206	Pedro de Toledo
__BRA__	35	SP	3537305	Penápolis
__BRA__	35	SP	3537404	Pereira Barreto
__BRA__	35	SP	3537503	Pereiras
__BRA__	35	SP	3537602	Peruíbe
__BRA__	35	SP	3537701	Piacatu
__BRA__	35	SP	3537800	Piedade
__BRA__	35	SP	3537909	Pilar do Sul
__BRA__	35	SP	3538006	Pindamonhangaba
__BRA__	35	SP	3538105	Pindorama
__BRA__	35	SP	3538204	Pinhalzinho
__BRA__	35	SP	3538303	Piquerobi
__BRA__	35	SP	3538501	Piquete
__BRA__	35	SP	3538600	Piracaia
__BRA__	35	SP	3538709	Piracicaba
__BRA__	35	SP	3538808	Piraju
__BRA__	35	SP	3538907	Pirajuí
__BRA__	35	SP	3539004	Pirangi
__BRA__	35	SP	3539103	Pirapora do Bom Jesus
__BRA__	35	SP	3539202	Pirapozinho
__BRA__	35	SP	3539301	Pirassununga
__BRA__	35	SP	3539400	Piratininga
__BRA__	35	SP	3539509	Pitangueiras
__BRA__	35	SP	3539608	Planalto
__BRA__	35	SP	3539707	Platina
__BRA__	35	SP	3539806	Poá
__BRA__	35	SP	3539905	Poloni
__BRA__	35	SP	3540002	Pompéia
__BRA__	35	SP	3540101	Pongaí
__BRA__	35	SP	3540200	Pontal
__BRA__	35	SP	3540259	Pontalinda
__BRA__	35	SP	3540309	Pontes Gestal
__BRA__	35	SP	3540408	Populina
__BRA__	35	SP	3540507	Porangaba
__BRA__	35	SP	3540606	Porto Feliz
__BRA__	35	SP	3540705	Porto Ferreira
__BRA__	35	SP	3540754	Potim
__BRA__	35	SP	3540804	Potirendaba
__BRA__	35	SP	3540853	Pracinha
__BRA__	35	SP	3540903	Pradópolis
__BRA__	35	SP	3541000	Praia Grande
__BRA__	35	SP	3541059	Pratânia
__BRA__	35	SP	3541109	Presidente Alves
__BRA__	35	SP	3541208	Presidente Bernardes
__BRA__	35	SP	3541307	Presidente Epitácio
__BRA__	35	SP	3541406	Presidente Prudente
__BRA__	35	SP	3541505	Presidente Venceslau
__BRA__	35	SP	3541604	Promissão
__BRA__	35	SP	3541653	Quadra
__BRA__	35	SP	3541703	Quatá
__BRA__	35	SP	3541802	Queiroz
__BRA__	35	SP	3541901	Queluz
__BRA__	35	SP	3542008	Quintana
__BRA__	35	SP	3542107	Rafard
__BRA__	35	SP	3542206	Rancharia
__BRA__	35	SP	3542305	Redenção da Serra
__BRA__	35	SP	3542404	Regente Feijó
__BRA__	35	SP	3542503	Reginópolis
__BRA__	35	SP	3542602	Registro
__BRA__	35	SP	3542701	Restinga
__BRA__	35	SP	3542800	Ribeira
__BRA__	35	SP	3542909	Ribeirão Bonito
__BRA__	35	SP	3543006	Ribeirão Branco
__BRA__	35	SP	3543105	Ribeirão Corrente
__BRA__	35	SP	3543204	Ribeirão do Sul
__BRA__	35	SP	3543238	Ribeirão dos Índios
__BRA__	35	SP	3543253	Ribeirão Grande
__BRA__	35	SP	3543303	Ribeirão Pires
__BRA__	35	SP	3543402	Ribeirão Preto
__BRA__	35	SP	3543600	Rifaina
__BRA__	35	SP	3543709	Rincão
__BRA__	35	SP	3543808	Rinópolis
__BRA__	35	SP	3543907	Rio Claro
__BRA__	35	SP	3544004	Rio das Pedras
__BRA__	35	SP	3544103	Rio Grande da Serra
__BRA__	35	SP	3544202	Riolândia
__BRA__	35	SP	3543501	Riversul
__BRA__	35	SP	3544251	Rosana
__BRA__	35	SP	3544301	Roseira
__BRA__	35	SP	3544400	Rubiácea
__BRA__	35	SP	3544509	Rubinéia
__BRA__	35	SP	3544608	Sabino
__BRA__	35	SP	3544707	Sagres
__BRA__	35	SP	3544806	Sales
__BRA__	35	SP	3544905	Sales Oliveira
__BRA__	35	SP	3545001	Salesópolis
__BRA__	35	SP	3545100	Salmourão
__BRA__	35	SP	3545159	Saltinho
__BRA__	35	SP	3545209	Salto
__BRA__	35	SP	3545308	Salto de Pirapora
__BRA__	35	SP	3545407	Salto Grande
__BRA__	35	SP	3545506	Sandovalina
__BRA__	35	SP	3545605	Santa Adélia
__BRA__	35	SP	3545704	Santa Albertina
__BRA__	35	SP	3545803	Santa Bárbara d'Oeste
__BRA__	35	SP	3546009	Santa Branca
__BRA__	35	SP	3546108	Santa Clara d'Oeste
__BRA__	35	SP	3546207	Santa Cruz da Conceição
__BRA__	35	SP	3546256	Santa Cruz da Esperança
__BRA__	35	SP	3546306	Santa Cruz das Palmeiras
__BRA__	35	SP	3546405	Santa Cruz do Rio Pardo
__BRA__	35	SP	3546504	Santa Ernestina
__BRA__	35	SP	3546603	Santa Fé do Sul
__BRA__	35	SP	3546702	Santa Gertrudes
__BRA__	35	SP	3546801	Santa Isabel
__BRA__	35	SP	3546900	Santa Lúcia
__BRA__	35	SP	3547007	Santa Maria da Serra
__BRA__	35	SP	3547106	Santa Mercedes
__BRA__	35	SP	3547502	Santa Rita do Passa Quatro
__BRA__	35	SP	3547403	Santa Rita d'Oeste
__BRA__	35	SP	3547601	Santa Rosa de Viterbo
__BRA__	35	SP	3547650	Santa Salete
__BRA__	35	SP	3547205	Santana da Ponte Pensa
__BRA__	35	SP	3547304	Santana de Parnaíba
__BRA__	35	SP	3547700	Santo Anastácio
__BRA__	35	SP	3547809	Santo André
__BRA__	35	SP	3547908	Santo Antônio da Alegria
__BRA__	35	SP	3548005	Santo Antônio de Posse
__BRA__	35	SP	3548054	Santo Antônio do Aracanguá
__BRA__	35	SP	3548104	Santo Antônio do Jardim
__BRA__	35	SP	3548203	Santo Antônio do Pinhal
__BRA__	35	SP	3548302	Santo Expedito
__BRA__	35	SP	3548401	Santópolis do Aguapeí
__BRA__	35	SP	3548500	Santos
__BRA__	35	SP	3548609	São Bento do Sapucaí
__BRA__	35	SP	3548708	São Bernardo do Campo
__BRA__	35	SP	3548807	São Caetano do Sul
__BRA__	35	SP	3548906	São Carlos
__BRA__	35	SP	3549003	São Francisco
__BRA__	35	SP	3549102	São João da Boa Vista
__BRA__	35	SP	3549201	São João das Duas Pontes
__BRA__	35	SP	3549250	São João de Iracema
__BRA__	35	SP	3549300	São João do Pau d'Alho
__BRA__	35	SP	3549409	São Joaquim da Barra
__BRA__	35	SP	3549508	São José da Bela Vista
__BRA__	35	SP	3549607	São José do Barreiro
__BRA__	35	SP	3549706	São José do Rio Pardo
__BRA__	35	SP	3549805	São José do Rio Preto
__BRA__	35	SP	3549904	São José dos Campos
__BRA__	35	SP	3549953	São Lourenço da Serra
__BRA__	35	SP	3550001	São Luís do Paraitinga
__BRA__	35	SP	3550100	São Manuel
__BRA__	35	SP	3550209	São Miguel Arcanjo
__BRA__	35	SP	3550308	São Paulo
__BRA__	35	SP	3550407	São Pedro
__BRA__	35	SP	3550506	São Pedro do Turvo
__BRA__	35	SP	3550605	São Roque
__BRA__	35	SP	3550704	São Sebastião
__BRA__	35	SP	3550803	São Sebastião da Grama
__BRA__	35	SP	3550902	São Simão
__BRA__	35	SP	3551009	São Vicente
__BRA__	35	SP	3551108	Sarapuí
__BRA__	35	SP	3551207	Sarutaiá
__BRA__	35	SP	3551306	Sebastianópolis do Sul
__BRA__	35	SP	3551405	Serra Azul
__BRA__	35	SP	3551603	Serra Negra
__BRA__	35	SP	3551504	Serrana
__BRA__	35	SP	3551702	Sertãozinho
__BRA__	35	SP	3551801	Sete Barras
__BRA__	35	SP	3551900	Severínia
__BRA__	35	SP	3552007	Silveiras
__BRA__	35	SP	3552106	Socorro
__BRA__	35	SP	3552205	Sorocaba
__BRA__	35	SP	3552304	Sud Mennucci
__BRA__	35	SP	3552403	Sumaré
__BRA__	35	SP	3552551	Suzanápolis
__BRA__	35	SP	3552502	Suzano
__BRA__	35	SP	3552601	Tabapuã
__BRA__	35	SP	3552700	Tabatinga
__BRA__	35	SP	3552809	Taboão da Serra
__BRA__	35	SP	3552908	Taciba
__BRA__	35	SP	3553005	Taguaí
__BRA__	35	SP	3553104	Taiaçu
__BRA__	35	SP	3553203	Taiúva
__BRA__	35	SP	3553302	Tambaú
__BRA__	35	SP	3553401	Tanabi
__BRA__	35	SP	3553500	Tapiraí
__BRA__	35	SP	3553609	Tapiratiba
__BRA__	35	SP	3553658	Taquaral
__BRA__	35	SP	3553708	Taquaritinga
__BRA__	35	SP	3553807	Taquarituba
__BRA__	35	SP	3553856	Taquarivaí
__BRA__	35	SP	3553906	Tarabai
__BRA__	35	SP	3553955	Tarumã
__BRA__	35	SP	3554003	Tatuí
__BRA__	35	SP	3554102	Taubaté
__BRA__	35	SP	3554201	Tejupá
__BRA__	35	SP	3554300	Teodoro Sampaio
__BRA__	35	SP	3554409	Terra Roxa
__BRA__	35	SP	3554508	Tietê
__BRA__	35	SP	3554607	Timburi
__BRA__	35	SP	3554656	Torre de Pedra
__BRA__	35	SP	3554706	Torrinha
__BRA__	35	SP	3554755	Trabiju
__BRA__	35	SP	3554805	Tremembé
__BRA__	35	SP	3554904	Três Fronteiras
__BRA__	35	SP	3554953	Tuiuti
__BRA__	35	SP	3555000	Tupã
__BRA__	35	SP	3555109	Tupi Paulista
__BRA__	35	SP	3555208	Turiúba
__BRA__	35	SP	3555307	Turmalina
__BRA__	35	SP	3555356	Ubarana
__BRA__	35	SP	3555406	Ubatuba
__BRA__	35	SP	3555505	Ubirajara
__BRA__	35	SP	3555604	Uchoa
__BRA__	35	SP	3555703	União Paulista
__BRA__	35	SP	3555802	Urânia
__BRA__	35	SP	3555901	Uru
__BRA__	35	SP	3556008	Urupês
__BRA__	35	SP	3556107	Valentim Gentil
__BRA__	35	SP	3556206	Valinhos
__BRA__	35	SP	3556305	Valparaíso
__BRA__	35	SP	3556354	Vargem
__BRA__	35	SP	3556404	Vargem Grande do Sul
__BRA__	35	SP	3556453	Vargem Grande Paulista
__BRA__	35	SP	3556503	Várzea Paulista
__BRA__	35	SP	3556602	Vera Cruz
__BRA__	35	SP	3556701	Vinhedo
__BRA__	35	SP	3556800	Viradouro
__BRA__	35	SP	3556909	Vista Alegre do Alto
__BRA__	35	SP	3556958	Vitória Brasil
__BRA__	35	SP	3557006	Votorantim
__BRA__	35	SP	3557105	Votuporanga
__BRA__	35	SP	3557154	Zacarias
__BRA__	31	MG	3100104	Abadia dos Dourados
__BRA__	31	MG	3100203	Abaeté
__BRA__	31	MG	3100302	Abre Campo
__BRA__	31	MG	3100401	Acaiaca
__BRA__	31	MG	3100500	Açucena
__BRA__	31	MG	3100609	Água Boa
__BRA__	31	MG	3100708	Água Comprida
__BRA__	31	MG	3100807	Aguanil
__BRA__	31	MG	3100906	Águas Formosas
__BRA__	31	MG	3101003	Águas Vermelhas
__BRA__	31	MG	3101102	Aimorés
__BRA__	31	MG	3101201	Aiuruoca
__BRA__	31	MG	3101300	Alagoa
__BRA__	31	MG	3101409	Albertina
__BRA__	31	MG	3101508	Além Paraíba
__BRA__	31	MG	3101607	Alfenas
__BRA__	31	MG	3101631	Alfredo Vasconcelos
__BRA__	31	MG	3101706	Almenara
__BRA__	31	MG	3101805	Alpercata
__BRA__	31	MG	3101904	Alpinópolis
__BRA__	31	MG	3102001	Alterosa
__BRA__	31	MG	3102050	Alto Caparaó
__BRA__	31	MG	3153509	Alto Jequitibá
__BRA__	31	MG	3102100	Alto Rio Doce
__BRA__	31	MG	3102209	Alvarenga
__BRA__	31	MG	3102308	Alvinópolis
__BRA__	31	MG	3102407	Alvorada de Minas
__BRA__	31	MG	3102506	Amparo do Serra
__BRA__	31	MG	3102605	Andradas
__BRA__	31	MG	3102803	Andrelândia
__BRA__	31	MG	3102852	Angelândia
__BRA__	31	MG	3102902	Antônio Carlos
__BRA__	31	MG	3103009	Antônio Dias
__BRA__	31	MG	3103108	Antônio Prado de Minas
__BRA__	31	MG	3103207	Araçaí
__BRA__	31	MG	3103306	Aracitaba
__BRA__	31	MG	3103405	Araçuaí
__BRA__	31	MG	3103504	Araguari
__BRA__	31	MG	3103603	Arantina
__BRA__	31	MG	3103702	Araponga
__BRA__	31	MG	3103751	Araporã
__BRA__	31	MG	3103801	Arapuá
__BRA__	31	MG	3103900	Araújos
__BRA__	31	MG	3104007	Araxá
__BRA__	31	MG	3104106	Arceburgo
__BRA__	31	MG	3104205	Arcos
__BRA__	31	MG	3104304	Areado
__BRA__	31	MG	3104403	Argirita
__BRA__	31	MG	3104452	Aricanduva
__BRA__	31	MG	3104502	Arinos
__BRA__	31	MG	3104601	Astolfo Dutra
__BRA__	31	MG	3104700	Ataléia
__BRA__	31	MG	3104809	Augusto de Lima
__BRA__	31	MG	3104908	Baependi
__BRA__	31	MG	3105004	Baldim
__BRA__	31	MG	3105103	Bambuí
__BRA__	31	MG	3105202	Bandeira
__BRA__	31	MG	3105301	Bandeira do Sul
__BRA__	31	MG	3105400	Barão de Cocais
__BRA__	31	MG	3105509	Barão de Monte Alto
__BRA__	31	MG	3105608	Barbacena
__BRA__	31	MG	3105707	Barra Longa
__BRA__	31	MG	3105905	Barroso
__BRA__	31	MG	3106002	Bela Vista de Minas
__BRA__	31	MG	3106101	Belmiro Braga
__BRA__	31	MG	3106200	Belo Horizonte
__BRA__	31	MG	3106309	Belo Oriente
__BRA__	31	MG	3106408	Belo Vale
__BRA__	31	MG	3106507	Berilo
__BRA__	31	MG	3106655	Berizal
__BRA__	31	MG	3106606	Bertópolis
__BRA__	31	MG	3106705	Betim
__BRA__	31	MG	3106804	Bias Fortes
__BRA__	31	MG	3106903	Bicas
__BRA__	31	MG	3107000	Biquinhas
__BRA__	31	MG	3107109	Boa Esperança
__BRA__	31	MG	3107208	Bocaina de Minas
__BRA__	31	MG	3107307	Bocaiúva
__BRA__	31	MG	3107406	Bom Despacho
__BRA__	31	MG	3107505	Bom Jardim de Minas
__BRA__	31	MG	3107604	Bom Jesus da Penha
__BRA__	31	MG	3107703	Bom Jesus do Amparo
__BRA__	31	MG	3107802	Bom Jesus do Galho
__BRA__	31	MG	3107901	Bom Repouso
__BRA__	31	MG	3108008	Bom Sucesso
__BRA__	31	MG	3108107	Bonfim
__BRA__	31	MG	3108206	Bonfinópolis de Minas
__BRA__	31	MG	3108255	Bonito de Minas
__BRA__	31	MG	3108305	Borda da Mata
__BRA__	31	MG	3108404	Botelhos
__BRA__	31	MG	3108503	Botumirim
__BRA__	31	MG	3108701	Brás Pires
__BRA__	31	MG	3108552	Brasilândia de Minas
__BRA__	31	MG	3108602	Brasília de Minas
__BRA__	31	MG	3108909	Brasópolis
__BRA__	31	MG	3108800	Braúnas
__BRA__	31	MG	3109006	Brumadinho
__BRA__	31	MG	3109105	Bueno Brandão
__BRA__	31	MG	3109204	Buenópolis
__BRA__	31	MG	3109253	Bugre
__BRA__	31	MG	3109303	Buritis
__BRA__	31	MG	3109402	Buritizeiro
__BRA__	31	MG	3109451	Cabeceira Grande
__BRA__	31	MG	3109501	Cabo Verde
__BRA__	31	MG	3109600	Cachoeira da Prata
__BRA__	31	MG	3109709	Cachoeira de Minas
__BRA__	31	MG	3102704	Cachoeira de Pajeú
__BRA__	31	MG	3109808	Cachoeira Dourada
__BRA__	31	MG	3109907	Caetanópolis
__BRA__	31	MG	3110004	Caeté
__BRA__	31	MG	3110103	Caiana
__BRA__	31	MG	3110202	Cajuri
__BRA__	31	MG	3110301	Caldas
__BRA__	31	MG	3110400	Camacho
__BRA__	31	MG	3110509	Camanducaia
__BRA__	31	MG	3110608	Cambuí
__BRA__	31	MG	3110707	Cambuquira
__BRA__	31	MG	3110806	Campanário
__BRA__	31	MG	3110905	Campanha
__BRA__	31	MG	3111002	Campestre
__BRA__	31	MG	3111101	Campina Verde
__BRA__	31	MG	3111150	Campo Azul
__BRA__	31	MG	3111200	Campo Belo
__BRA__	31	MG	3111309	Campo do Meio
__BRA__	31	MG	3111408	Campo Florido
__BRA__	31	MG	3111507	Campos Altos
__BRA__	31	MG	3111606	Campos Gerais
__BRA__	31	MG	3111903	Cana Verde
__BRA__	31	MG	3111705	Canaã
__BRA__	31	MG	3111804	Canápolis
__BRA__	31	MG	3112000	Candeias
__BRA__	31	MG	3112059	Cantagalo
__BRA__	31	MG	3112109	Caparaó
__BRA__	31	MG	3112208	Capela Nova
__BRA__	31	MG	3112307	Capelinha
__BRA__	31	MG	3112406	Capetinga
__BRA__	31	MG	3112505	Capim Branco
__BRA__	31	MG	3112604	Capinópolis
__BRA__	31	MG	3112653	Capitão Andrade
__BRA__	31	MG	3112703	Capitão Enéas
__BRA__	31	MG	3112802	Capitólio
__BRA__	31	MG	3112901	Caputira
__BRA__	31	MG	3113008	Caraí
__BRA__	31	MG	3113107	Caranaíba
__BRA__	31	MG	3113206	Carandaí
__BRA__	31	MG	3113305	Carangola
__BRA__	31	MG	3113404	Caratinga
__BRA__	31	MG	3113503	Carbonita
__BRA__	31	MG	3113602	Careaçu
__BRA__	31	MG	3113701	Carlos Chagas
__BRA__	31	MG	3113800	Carmésia
__BRA__	31	MG	3113909	Carmo da Cachoeira
__BRA__	31	MG	3114006	Carmo da Mata
__BRA__	31	MG	3114105	Carmo de Minas
__BRA__	31	MG	3114204	Carmo do Cajuru
__BRA__	31	MG	3114303	Carmo do Paranaíba
__BRA__	31	MG	3114402	Carmo do Rio Claro
__BRA__	31	MG	3114501	Carmópolis de Minas
__BRA__	31	MG	3114550	Carneirinho
__BRA__	31	MG	3114600	Carrancas
__BRA__	31	MG	3114709	Carvalhópolis
__BRA__	31	MG	3114808	Carvalhos
__BRA__	31	MG	3114907	Casa Grande
__BRA__	31	MG	3115003	Cascalho Rico
__BRA__	31	MG	3115102	Cássia
__BRA__	31	MG	3115300	Cataguases
__BRA__	31	MG	3115359	Catas Altas
__BRA__	31	MG	3115409	Catas Altas da Noruega
__BRA__	31	MG	3115458	Catuji
__BRA__	31	MG	3115474	Catuti
__BRA__	31	MG	3115508	Caxambu
__BRA__	31	MG	3115607	Cedro do Abaeté
__BRA__	31	MG	3115706	Central de Minas
__BRA__	31	MG	3115805	Centralina
__BRA__	31	MG	3115904	Chácara
__BRA__	31	MG	3116001	Chalé
__BRA__	31	MG	3116100	Chapada do Norte
__BRA__	31	MG	3116159	Chapada Gaúcha
__BRA__	31	MG	3116209	Chiador
__BRA__	31	MG	3116308	Cipotânea
__BRA__	31	MG	3116407	Claraval
__BRA__	31	MG	3116506	Claro dos Poções
__BRA__	31	MG	3116605	Cláudio
__BRA__	31	MG	3116704	Coimbra
__BRA__	31	MG	3116803	Coluna
__BRA__	31	MG	3116902	Comendador Gomes
__BRA__	31	MG	3117009	Comercinho
__BRA__	31	MG	3117108	Conceição da Aparecida
__BRA__	31	MG	3115201	Conceição da Barra de Minas
__BRA__	31	MG	3117306	Conceição das Alagoas
__BRA__	31	MG	3117207	Conceição das Pedras
__BRA__	31	MG	3117405	Conceição de Ipanema
__BRA__	31	MG	3117504	Conceição do Mato Dentro
__BRA__	31	MG	3117603	Conceição do Pará
__BRA__	31	MG	3117702	Conceição do Rio Verde
__BRA__	31	MG	3117801	Conceição dos Ouros
__BRA__	31	MG	3117836	Cônego Marinho
__BRA__	31	MG	3117876	Confins
__BRA__	31	MG	3117900	Congonhal
__BRA__	31	MG	3118007	Congonhas
__BRA__	31	MG	3118106	Congonhas do Norte
__BRA__	31	MG	3118205	Conquista
__BRA__	31	MG	3118304	Conselheiro Lafaiete
__BRA__	31	MG	3118403	Conselheiro Pena
__BRA__	31	MG	3118502	Consolação
__BRA__	31	MG	3118601	Contagem
__BRA__	31	MG	3118700	Coqueiral
__BRA__	31	MG	3118809	Coração de Jesus
__BRA__	31	MG	3118908	Cordisburgo
__BRA__	31	MG	3119005	Cordislândia
__BRA__	31	MG	3119104	Corinto
__BRA__	31	MG	3119203	Coroaci
__BRA__	31	MG	3119302	Coromandel
__BRA__	31	MG	3119401	Coronel Fabriciano
__BRA__	31	MG	3119500	Coronel Murta
__BRA__	31	MG	3119609	Coronel Pacheco
__BRA__	31	MG	3119708	Coronel Xavier Chaves
__BRA__	31	MG	3119807	Córrego Danta
__BRA__	31	MG	3119906	Córrego do Bom Jesus
__BRA__	31	MG	3119955	Córrego Fundo
__BRA__	31	MG	3120003	Córrego Novo
__BRA__	31	MG	3120102	Couto de Magalhães de Minas
__BRA__	31	MG	3120151	Crisólita
__BRA__	31	MG	3120201	Cristais
__BRA__	31	MG	3120300	Cristália
__BRA__	31	MG	3120409	Cristiano Otoni
__BRA__	31	MG	3120508	Cristina
__BRA__	31	MG	3120607	Crucilândia
__BRA__	31	MG	3120706	Cruzeiro da Fortaleza
__BRA__	31	MG	3120805	Cruzília
__BRA__	31	MG	3120839	Cuparaque
__BRA__	31	MG	3120870	Curral de Dentro
__BRA__	31	MG	3120904	Curvelo
__BRA__	31	MG	3121001	Datas
__BRA__	31	MG	3121100	Delfim Moreira
__BRA__	31	MG	3121209	Delfinópolis
__BRA__	31	MG	3121258	Delta
__BRA__	31	MG	3121308	Descoberto
__BRA__	31	MG	3121407	Desterro de Entre Rios
__BRA__	31	MG	3121506	Desterro do Melo
__BRA__	31	MG	3121605	Diamantina
__BRA__	31	MG	3121704	Diogo de Vasconcelos
__BRA__	31	MG	3121803	Dionísio
__BRA__	31	MG	3121902	Divinésia
__BRA__	31	MG	3122009	Divino
__BRA__	31	MG	3122108	Divino das Laranjeiras
__BRA__	31	MG	3122207	Divinolândia de Minas
__BRA__	31	MG	3122306	Divinópolis
__BRA__	31	MG	3122355	Divisa Alegre
__BRA__	31	MG	3122405	Divisa Nova
__BRA__	31	MG	3122454	Divisópolis
__BRA__	31	MG	3122470	Dom Bosco
__BRA__	31	MG	3122504	Dom Cavati
__BRA__	31	MG	3122603	Dom Joaquim
__BRA__	31	MG	3122702	Dom Silvério
__BRA__	31	MG	3122801	Dom Viçoso
__BRA__	31	MG	3122900	Dona Eusébia
__BRA__	31	MG	3123007	Dores de Campos
__BRA__	31	MG	3123106	Dores de Guanhães
__BRA__	31	MG	3123205	Dores do Indaiá
__BRA__	31	MG	3123304	Dores do Turvo
__BRA__	31	MG	3123403	Doresópolis
__BRA__	31	MG	3123502	Douradoquara
__BRA__	31	MG	3123528	Durandé
__BRA__	31	MG	3123601	Elói Mendes
__BRA__	31	MG	3123700	Engenheiro Caldas
__BRA__	31	MG	3123809	Engenheiro Navarro
__BRA__	31	MG	3123858	Entre Folhas
__BRA__	31	MG	3123908	Entre Rios de Minas
__BRA__	31	MG	3124005	Ervália
__BRA__	31	MG	3124104	Esmeraldas
__BRA__	31	MG	3124203	Espera Feliz
__BRA__	31	MG	3124302	Espinosa
__BRA__	31	MG	3124401	Espírito Santo do Dourado
__BRA__	31	MG	3124500	Estiva
__BRA__	31	MG	3124609	Estrela Dalva
__BRA__	31	MG	3124708	Estrela do Indaiá
__BRA__	31	MG	3124807	Estrela do Sul
__BRA__	31	MG	3124906	Eugenópolis
__BRA__	31	MG	3125002	Ewbank da Câmara
__BRA__	31	MG	3125101	Extrema
__BRA__	31	MG	3125200	Fama
__BRA__	31	MG	3125309	Faria Lemos
__BRA__	31	MG	3125408	Felício dos Santos
__BRA__	31	MG	3125606	Felisburgo
__BRA__	31	MG	3125705	Felixlândia
__BRA__	31	MG	3125804	Fernandes Tourinho
__BRA__	31	MG	3125903	Ferros
__BRA__	31	MG	3125952	Fervedouro
__BRA__	31	MG	3126000	Florestal
__BRA__	31	MG	3126109	Formiga
__BRA__	31	MG	3126208	Formoso
__BRA__	31	MG	3126307	Fortaleza de Minas
__BRA__	31	MG	3126406	Fortuna de Minas
__BRA__	31	MG	3126505	Francisco Badaró
__BRA__	31	MG	3126604	Francisco Dumont
__BRA__	31	MG	3126703	Francisco Sá
__BRA__	31	MG	3126752	Franciscópolis
__BRA__	31	MG	3126802	Frei Gaspar
__BRA__	31	MG	3126901	Frei Inocêncio
__BRA__	31	MG	3126950	Frei Lagonegro
__BRA__	31	MG	3127008	Fronteira
__BRA__	31	MG	3127057	Fronteira dos Vales
__BRA__	31	MG	3127073	Fruta de Leite
__BRA__	31	MG	3127107	Frutal
__BRA__	31	MG	3127206	Funilândia
__BRA__	31	MG	3127305	Galiléia
__BRA__	31	MG	3127339	Gameleiras
__BRA__	31	MG	3127354	Glaucilândia
__BRA__	31	MG	3127370	Goiabeira
__BRA__	31	MG	3127388	Goianá
__BRA__	31	MG	3127404	Gonçalves
__BRA__	31	MG	3127503	Gonzaga
__BRA__	31	MG	3127602	Gouveia
__BRA__	31	MG	3127701	Governador Valadares
__BRA__	31	MG	3127800	Grão Mogol
__BRA__	31	MG	3127909	Grupiara
__BRA__	31	MG	3128006	Guanhães
__BRA__	31	MG	3128105	Guapé
__BRA__	31	MG	3128204	Guaraciaba
__BRA__	31	MG	3128253	Guaraciama
__BRA__	31	MG	3128303	Guaranésia
__BRA__	31	MG	3128402	Guarani
__BRA__	31	MG	3128501	Guarará
__BRA__	31	MG	3128600	Guarda-Mor
__BRA__	31	MG	3128709	Guaxupé
__BRA__	31	MG	3128808	Guidoval
__BRA__	31	MG	3128907	Guimarânia
__BRA__	31	MG	3129004	Guiricema
__BRA__	31	MG	3129103	Gurinhatã
__BRA__	31	MG	3129202	Heliodora
__BRA__	31	MG	3129301	Iapu
__BRA__	31	MG	3129400	Ibertioga
__BRA__	31	MG	3129509	Ibiá
__BRA__	31	MG	3129608	Ibiaí
__BRA__	31	MG	3129657	Ibiracatu
__BRA__	31	MG	3129707	Ibiraci
__BRA__	31	MG	3129806	Ibirité
__BRA__	31	MG	3129905	Ibitiúra de Minas
__BRA__	31	MG	3130002	Ibituruna
__BRA__	31	MG	3130051	Icaraí de Minas
__BRA__	31	MG	3130101	Igarapé
__BRA__	31	MG	3130200	Igaratinga
__BRA__	31	MG	3130309	Iguatama
__BRA__	31	MG	3130408	Ijaci
__BRA__	31	MG	3130507	Ilicínea
__BRA__	31	MG	3130556	Imbé de Minas
__BRA__	31	MG	3130606	Inconfidentes
__BRA__	31	MG	3130655	Indaiabira
__BRA__	31	MG	3130705	Indianópolis
__BRA__	31	MG	3130804	Ingaí
__BRA__	31	MG	3130903	Inhapim
__BRA__	31	MG	3131000	Inhaúma
__BRA__	31	MG	3131109	Inimutaba
__BRA__	31	MG	3131158	Ipaba
__BRA__	31	MG	3131208	Ipanema
__BRA__	31	MG	3131307	Ipatinga
__BRA__	31	MG	3131406	Ipiaçu
__BRA__	31	MG	3131505	Ipuiúna
__BRA__	31	MG	3131604	Iraí de Minas
__BRA__	31	MG	3131703	Itabira
__BRA__	31	MG	3131802	Itabirinha
__BRA__	31	MG	3131901	Itabirito
__BRA__	31	MG	3132008	Itacambira
__BRA__	31	MG	3132107	Itacarambi
__BRA__	31	MG	3132206	Itaguara
__BRA__	31	MG	3132305	Itaipé
__BRA__	31	MG	3132404	Itajubá
__BRA__	31	MG	3132503	Itamarandiba
__BRA__	31	MG	3132602	Itamarati de Minas
__BRA__	31	MG	3132701	Itambacuri
__BRA__	31	MG	3132800	Itambé do Mato Dentro
__BRA__	31	MG	3132909	Itamogi
__BRA__	31	MG	3133006	Itamonte
__BRA__	31	MG	3133105	Itanhandu
__BRA__	31	MG	3133204	Itanhomi
__BRA__	31	MG	3133303	Itaobim
__BRA__	31	MG	3133402	Itapagipe
__BRA__	31	MG	3133501	Itapecerica
__BRA__	31	MG	3133600	Itapeva
__BRA__	31	MG	3133709	Itatiaiuçu
__BRA__	31	MG	3133758	Itaú de Minas
__BRA__	31	MG	3133808	Itaúna
__BRA__	31	MG	3133907	Itaverava
__BRA__	31	MG	3134004	Itinga
__BRA__	31	MG	3134103	Itueta
__BRA__	31	MG	3134202	Ituiutaba
__BRA__	31	MG	3134301	Itumirim
__BRA__	31	MG	3134400	Iturama
__BRA__	31	MG	3134509	Itutinga
__BRA__	31	MG	3134608	Jaboticatubas
__BRA__	31	MG	3134707	Jacinto
__BRA__	31	MG	3134806	Jacuí
__BRA__	31	MG	3134905	Jacutinga
__BRA__	31	MG	3135001	Jaguaraçu
__BRA__	31	MG	3135050	Jaíba
__BRA__	31	MG	3135076	Jampruca
__BRA__	31	MG	3135100	Janaúba
__BRA__	31	MG	3135209	Januária
__BRA__	31	MG	3135308	Japaraíba
__BRA__	31	MG	3135357	Japonvar
__BRA__	31	MG	3135407	Jeceaba
__BRA__	31	MG	3135456	Jenipapo de Minas
__BRA__	31	MG	3135506	Jequeri
__BRA__	31	MG	3135605	Jequitaí
__BRA__	31	MG	3135704	Jequitibá
__BRA__	31	MG	3135803	Jequitinhonha
__BRA__	31	MG	3135902	Jesuânia
__BRA__	31	MG	3136009	Joaíma
__BRA__	31	MG	3136108	Joanésia
__BRA__	31	MG	3136207	João Monlevade
__BRA__	31	MG	3136306	João Pinheiro
__BRA__	31	MG	3136405	Joaquim Felício
__BRA__	31	MG	3136504	Jordânia
__BRA__	31	MG	3136520	José Gonçalves de Minas
__BRA__	31	MG	3136553	José Raydan
__BRA__	31	MG	3136579	Josenópolis
__BRA__	31	MG	3136652	Juatuba
__BRA__	31	MG	3136702	Juiz de Fora
__BRA__	31	MG	3136801	Juramento
__BRA__	31	MG	3136900	Juruaia
__BRA__	31	MG	3136959	Juvenília
__BRA__	31	MG	3137007	Ladainha
__BRA__	31	MG	3137106	Lagamar
__BRA__	31	MG	3137205	Lagoa da Prata
__BRA__	31	MG	3137304	Lagoa dos Patos
__BRA__	31	MG	3137403	Lagoa Dourada
__BRA__	31	MG	3137502	Lagoa Formosa
__BRA__	31	MG	3137536	Lagoa Grande
__BRA__	31	MG	3137601	Lagoa Santa
__BRA__	31	MG	3137700	Lajinha
__BRA__	31	MG	3137809	Lambari
__BRA__	31	MG	3137908	Lamim
__BRA__	31	MG	3138005	Laranjal
__BRA__	31	MG	3138104	Lassance
__BRA__	31	MG	3138203	Lavras
__BRA__	31	MG	3138302	Leandro Ferreira
__BRA__	31	MG	3138351	Leme do Prado
__BRA__	31	MG	3138401	Leopoldina
__BRA__	31	MG	3138500	Liberdade
__BRA__	31	MG	3138609	Lima Duarte
__BRA__	31	MG	3138625	Limeira do Oeste
__BRA__	31	MG	3138658	Lontra
__BRA__	31	MG	3138674	Luisburgo
__BRA__	31	MG	3138682	Luislândia
__BRA__	31	MG	3138708	Luminárias
__BRA__	31	MG	3138807	Luz
__BRA__	31	MG	3138906	Machacalis
__BRA__	31	MG	3139003	Machado
__BRA__	31	MG	3139102	Madre de Deus de Minas
__BRA__	31	MG	3139201	Malacacheta
__BRA__	31	MG	3139250	Mamonas
__BRA__	31	MG	3139300	Manga
__BRA__	31	MG	3139409	Manhuaçu
__BRA__	31	MG	3139508	Manhumirim
__BRA__	31	MG	3139607	Mantena
__BRA__	31	MG	3139805	Mar de Espanha
__BRA__	31	MG	3139706	Maravilhas
__BRA__	31	MG	3139904	Maria da Fé
__BRA__	31	MG	3140001	Mariana
__BRA__	31	MG	3140100	Marilac
__BRA__	31	MG	3140159	Mário Campos
__BRA__	31	MG	3140209	Maripá de Minas
__BRA__	31	MG	3140308	Marliéria
__BRA__	31	MG	3140407	Marmelópolis
__BRA__	31	MG	3140506	Martinho Campos
__BRA__	31	MG	3140530	Martins Soares
__BRA__	31	MG	3140555	Mata Verde
__BRA__	31	MG	3140605	Materlândia
__BRA__	31	MG	3140704	Mateus Leme
__BRA__	31	MG	3171501	Mathias Lobato
__BRA__	31	MG	3140803	Matias Barbosa
__BRA__	31	MG	3140852	Matias Cardoso
__BRA__	31	MG	3140902	Matipó
__BRA__	31	MG	3141009	Mato Verde
__BRA__	31	MG	3141108	Matozinhos
__BRA__	31	MG	3141207	Matutina
__BRA__	31	MG	3141306	Medeiros
__BRA__	31	MG	3141405	Medina
__BRA__	31	MG	3141504	Mendes Pimentel
__BRA__	31	MG	3141603	Mercês
__BRA__	31	MG	3141702	Mesquita
__BRA__	31	MG	3141801	Minas Novas
__BRA__	31	MG	3141900	Minduri
__BRA__	31	MG	3142007	Mirabela
__BRA__	31	MG	3142106	Miradouro
__BRA__	31	MG	3142205	Miraí
__BRA__	31	MG	3142254	Miravânia
__BRA__	31	MG	3142304	Moeda
__BRA__	31	MG	3142403	Moema
__BRA__	31	MG	3142502	Monjolos
__BRA__	31	MG	3142601	Monsenhor Paulo
__BRA__	31	MG	3142700	Montalvânia
__BRA__	31	MG	3142809	Monte Alegre de Minas
__BRA__	31	MG	3142908	Monte Azul
__BRA__	31	MG	3143005	Monte Belo
__BRA__	31	MG	3143104	Monte Carmelo
__BRA__	31	MG	3143153	Monte Formoso
__BRA__	31	MG	3143203	Monte Santo de Minas
__BRA__	31	MG	3143401	Monte Sião
__BRA__	31	MG	3143302	Montes Claros
__BRA__	31	MG	3143450	Montezuma
__BRA__	31	MG	3143500	Morada Nova de Minas
__BRA__	31	MG	3143609	Morro da Garça
__BRA__	31	MG	3143708	Morro do Pilar
__BRA__	31	MG	3143807	Munhoz
__BRA__	31	MG	3143906	Muriaé
__BRA__	31	MG	3144003	Mutum
__BRA__	31	MG	3144102	Muzambinho
__BRA__	31	MG	3144201	Nacip Raydan
__BRA__	31	MG	3144300	Nanuque
__BRA__	31	MG	3144359	Naque
__BRA__	31	MG	3144375	Natalândia
__BRA__	31	MG	3144409	Natércia
__BRA__	31	MG	3144508	Nazareno
__BRA__	31	MG	3144607	Nepomuceno
__BRA__	31	MG	3144656	Ninheira
__BRA__	31	MG	3144672	Nova Belém
__BRA__	31	MG	3144706	Nova Era
__BRA__	31	MG	3144805	Nova Lima
__BRA__	31	MG	3144904	Nova Módica
__BRA__	31	MG	3145000	Nova Ponte
__BRA__	31	MG	3145059	Nova Porteirinha
__BRA__	31	MG	3145109	Nova Resende
__BRA__	31	MG	3145208	Nova Serrana
__BRA__	31	MG	3136603	Nova União
__BRA__	31	MG	3145307	Novo Cruzeiro
__BRA__	31	MG	3145356	Novo Oriente de Minas
__BRA__	31	MG	3145372	Novorizonte
__BRA__	31	MG	3145406	Olaria
__BRA__	31	MG	3145455	Olhos-d'Água
__BRA__	31	MG	3145505	Olímpio Noronha
__BRA__	31	MG	3145604	Oliveira
__BRA__	31	MG	3145703	Oliveira Fortes
__BRA__	31	MG	3145802	Onça de Pitangui
__BRA__	31	MG	3145851	Oratórios
__BRA__	31	MG	3145877	Orizânia
__BRA__	31	MG	3145901	Ouro Branco
__BRA__	31	MG	3146008	Ouro Fino
__BRA__	31	MG	3146107	Ouro Preto
__BRA__	31	MG	3146206	Ouro Verde de Minas
__BRA__	31	MG	3146255	Padre Carvalho
__BRA__	31	MG	3146305	Padre Paraíso
__BRA__	31	MG	3146552	Pai Pedro
__BRA__	31	MG	3146404	Paineiras
__BRA__	31	MG	3146503	Pains
__BRA__	31	MG	3146602	Paiva
__BRA__	31	MG	3146701	Palma
__BRA__	31	MG	3146750	Palmópolis
__BRA__	31	MG	3146909	Papagaios
__BRA__	31	MG	3147105	Pará de Minas
__BRA__	31	MG	3147006	Paracatu
__BRA__	31	MG	3147204	Paraguaçu
__BRA__	31	MG	3147303	Paraisópolis
__BRA__	31	MG	3147402	Paraopeba
__BRA__	31	MG	3147600	Passa Quatro
__BRA__	31	MG	3147709	Passa Tempo
__BRA__	31	MG	3147501	Passabém
__BRA__	31	MG	3147808	Passa-Vinte
__BRA__	31	MG	3147907	Passos
__BRA__	31	MG	3147956	Patis
__BRA__	31	MG	3148004	Patos de Minas
__BRA__	31	MG	3148103	Patrocínio
__BRA__	31	MG	3148202	Patrocínio do Muriaé
__BRA__	31	MG	3148301	Paula Cândido
__BRA__	31	MG	3148400	Paulistas
__BRA__	31	MG	3148509	Pavão
__BRA__	31	MG	3148608	Peçanha
__BRA__	31	MG	3148707	Pedra Azul
__BRA__	31	MG	3148756	Pedra Bonita
__BRA__	31	MG	3148806	Pedra do Anta
__BRA__	31	MG	3148905	Pedra do Indaiá
__BRA__	31	MG	3149002	Pedra Dourada
__BRA__	31	MG	3149101	Pedralva
__BRA__	31	MG	3149150	Pedras de Maria da Cruz
__BRA__	31	MG	3149200	Pedrinópolis
__BRA__	31	MG	3149309	Pedro Leopoldo
__BRA__	31	MG	3149408	Pedro Teixeira
__BRA__	31	MG	3149507	Pequeri
__BRA__	31	MG	3149606	Pequi
__BRA__	31	MG	3149705	Perdigão
__BRA__	31	MG	3149804	Perdizes
__BRA__	31	MG	3149903	Perdões
__BRA__	31	MG	3149952	Periquito
__BRA__	31	MG	3150000	Pescador
__BRA__	31	MG	3150109	Piau
__BRA__	31	MG	3150158	Piedade de Caratinga
__BRA__	31	MG	3150208	Piedade de Ponte Nova
__BRA__	31	MG	3150307	Piedade do Rio Grande
__BRA__	31	MG	3150406	Piedade dos Gerais
__BRA__	31	MG	3150505	Pimenta
__BRA__	31	MG	3150539	Pingo-d'Água
__BRA__	31	MG	3150570	Pintópolis
__BRA__	31	MG	3150604	Piracema
__BRA__	31	MG	3150703	Pirajuba
__BRA__	31	MG	3150802	Piranga
__BRA__	31	MG	3150901	Piranguçu
__BRA__	31	MG	3151008	Piranguinho
__BRA__	31	MG	3151107	Pirapetinga
__BRA__	31	MG	3151206	Pirapora
__BRA__	31	MG	3151305	Piraúba
__BRA__	31	MG	3151404	Pitangui
__BRA__	31	MG	3151503	Piumhi
__BRA__	31	MG	3151602	Planura
__BRA__	31	MG	3151701	Poço Fundo
__BRA__	31	MG	3151800	Poços de Caldas
__BRA__	31	MG	3151909	Pocrane
__BRA__	31	MG	3152006	Pompéu
__BRA__	31	MG	3152105	Ponte Nova
__BRA__	31	MG	3152131	Ponto Chique
__BRA__	31	MG	3152170	Ponto dos Volantes
__BRA__	31	MG	3152204	Porteirinha
__BRA__	31	MG	3152303	Porto Firme
__BRA__	31	MG	3152402	Poté
__BRA__	31	MG	3152501	Pouso Alegre
__BRA__	31	MG	3152600	Pouso Alto
__BRA__	31	MG	3152709	Prados
__BRA__	31	MG	3152808	Prata
__BRA__	31	MG	3152907	Pratápolis
__BRA__	31	MG	3153004	Pratinha
__BRA__	31	MG	3153103	Presidente Bernardes
__BRA__	31	MG	3153202	Presidente Juscelino
__BRA__	31	MG	3153301	Presidente Kubitschek
__BRA__	31	MG	3153400	Presidente Olegário
__BRA__	31	MG	3153608	Prudente de Morais
__BRA__	31	MG	3153707	Quartel Geral
__BRA__	31	MG	3153806	Queluzito
__BRA__	31	MG	3153905	Raposos
__BRA__	31	MG	3154002	Raul Soares
__BRA__	31	MG	3154101	Recreio
__BRA__	31	MG	3154150	Reduto
__BRA__	31	MG	3154200	Resende Costa
__BRA__	31	MG	3154309	Resplendor
__BRA__	31	MG	3154408	Ressaquinha
__BRA__	31	MG	3154457	Riachinho
__BRA__	31	MG	3154507	Riacho dos Machados
__BRA__	31	MG	3154606	Ribeirão das Neves
__BRA__	31	MG	3154705	Ribeirão Vermelho
__BRA__	31	MG	3154804	Rio Acima
__BRA__	31	MG	3154903	Rio Casca
__BRA__	31	MG	3155108	Rio do Prado
__BRA__	31	MG	3155009	Rio Doce
__BRA__	31	MG	3155207	Rio Espera
__BRA__	31	MG	3155306	Rio Manso
__BRA__	31	MG	3155405	Rio Novo
__BRA__	31	MG	3155504	Rio Paranaíba
__BRA__	31	MG	3155603	Rio Pardo de Minas
__BRA__	31	MG	3155702	Rio Piracicaba
__BRA__	31	MG	3155801	Rio Pomba
__BRA__	31	MG	3155900	Rio Preto
__BRA__	31	MG	3156007	Rio Vermelho
__BRA__	31	MG	3156106	Ritápolis
__BRA__	31	MG	3156205	Rochedo de Minas
__BRA__	31	MG	3156304	Rodeiro
__BRA__	31	MG	3156403	Romaria
__BRA__	31	MG	3156452	Rosário da Limeira
__BRA__	31	MG	3156502	Rubelita
__BRA__	31	MG	3156601	Rubim
__BRA__	31	MG	3156700	Sabará
__BRA__	31	MG	3156809	Sabinópolis
__BRA__	31	MG	3156908	Sacramento
__BRA__	31	MG	3157005	Salinas
__BRA__	31	MG	3157104	Salto da Divisa
__BRA__	31	MG	3157203	Santa Bárbara
__BRA__	31	MG	3157252	Santa Bárbara do Leste
__BRA__	31	MG	3157278	Santa Bárbara do Monte Verde
__BRA__	31	MG	3157302	Santa Bárbara do Tugúrio
__BRA__	31	MG	3157336	Santa Cruz de Minas
__BRA__	31	MG	3157377	Santa Cruz de Salinas
__BRA__	31	MG	3157401	Santa Cruz do Escalvado
__BRA__	31	MG	3157500	Santa Efigênia de Minas
__BRA__	31	MG	3157609	Santa Fé de Minas
__BRA__	31	MG	3157658	Santa Helena de Minas
__BRA__	31	MG	3157708	Santa Juliana
__BRA__	31	MG	3157807	Santa Luzia
__BRA__	31	MG	3157906	Santa Margarida
__BRA__	31	MG	3158003	Santa Maria de Itabira
__BRA__	31	MG	3158102	Santa Maria do Salto
__BRA__	31	MG	3158201	Santa Maria do Suaçuí
__BRA__	31	MG	3159209	Santa Rita de Caldas
__BRA__	31	MG	3159407	Santa Rita de Ibitipoca
__BRA__	31	MG	3159308	Santa Rita de Jacutinga
__BRA__	31	MG	3159357	Santa Rita de Minas
__BRA__	31	MG	3159506	Santa Rita do Itueto
__BRA__	31	MG	3159605	Santa Rita do Sapucaí
__BRA__	31	MG	3159704	Santa Rosa da Serra
__BRA__	31	MG	3159803	Santa Vitória
__BRA__	31	MG	3158300	Santana da Vargem
__BRA__	31	MG	3158409	Santana de Cataguases
__BRA__	31	MG	3158508	Santana de Pirapama
__BRA__	31	MG	3158607	Santana do Deserto
__BRA__	31	MG	3158706	Santana do Garambéu
__BRA__	31	MG	3158805	Santana do Jacaré
__BRA__	31	MG	3158904	Santana do Manhuaçu
__BRA__	31	MG	3158953	Santana do Paraíso
__BRA__	31	MG	3159001	Santana do Riacho
__BRA__	31	MG	3159100	Santana dos Montes
__BRA__	31	MG	3159902	Santo Antônio do Amparo
__BRA__	31	MG	3160009	Santo Antônio do Aventureiro
__BRA__	31	MG	3160108	Santo Antônio do Grama
__BRA__	31	MG	3160207	Santo Antônio do Itambé
__BRA__	31	MG	3160306	Santo Antônio do Jacinto
__BRA__	31	MG	3160405	Santo Antônio do Monte
__BRA__	31	MG	3160454	Santo Antônio do Retiro
__BRA__	31	MG	3160504	Santo Antônio do Rio Abaixo
__BRA__	31	MG	3160603	Santo Hipólito
__BRA__	31	MG	3160702	Santos Dumont
__BRA__	31	MG	3160801	São Bento Abade
__BRA__	31	MG	3160900	São Brás do Suaçuí
__BRA__	31	MG	3160959	São Domingos das Dores
__BRA__	31	MG	3161007	São Domingos do Prata
__BRA__	31	MG	3161056	São Félix de Minas
__BRA__	31	MG	3161106	São Francisco
__BRA__	31	MG	3161205	São Francisco de Paula
__BRA__	31	MG	3161304	São Francisco de Sales
__BRA__	31	MG	3161403	São Francisco do Glória
__BRA__	31	MG	3161502	São Geraldo
__BRA__	31	MG	3161601	São Geraldo da Piedade
__BRA__	31	MG	3161650	São Geraldo do Baixio
__BRA__	31	MG	3161700	São Gonçalo do Abaeté
__BRA__	31	MG	3161809	São Gonçalo do Pará
__BRA__	31	MG	3161908	São Gonçalo do Rio Abaixo
__BRA__	31	MG	3125507	São Gonçalo do Rio Preto
__BRA__	31	MG	3162005	São Gonçalo do Sapucaí
__BRA__	31	MG	3162104	São Gotardo
__BRA__	31	MG	3162203	São João Batista do Glória
__BRA__	31	MG	3162252	São João da Lagoa
__BRA__	31	MG	3162302	São João da Mata
__BRA__	31	MG	3162401	São João da Ponte
__BRA__	31	MG	3162450	São João das Missões
__BRA__	31	MG	3162500	São João del Rei
__BRA__	31	MG	3162559	São João do Manhuaçu
__BRA__	31	MG	3162575	São João do Manteninha
__BRA__	31	MG	3162609	São João do Oriente
__BRA__	31	MG	3162658	São João do Pacuí
__BRA__	31	MG	3162708	São João do Paraíso
__BRA__	31	MG	3162807	São João Evangelista
__BRA__	31	MG	3162906	São João Nepomuceno
__BRA__	31	MG	3162922	São Joaquim de Bicas
__BRA__	31	MG	3162948	São José da Barra
__BRA__	31	MG	3162955	São José da Lapa
__BRA__	31	MG	3163003	São José da Safira
__BRA__	31	MG	3163102	São José da Varginha
__BRA__	31	MG	3163201	São José do Alegre
__BRA__	31	MG	3163300	São José do Divino
__BRA__	31	MG	3163409	São José do Goiabal
__BRA__	31	MG	3163508	São José do Jacuri
__BRA__	31	MG	3163607	São José do Mantimento
__BRA__	31	MG	3163706	São Lourenço
__BRA__	31	MG	3163805	São Miguel do Anta
__BRA__	31	MG	3163904	São Pedro da União
__BRA__	31	MG	3164100	São Pedro do Suaçuí
__BRA__	31	MG	3164001	São Pedro dos Ferros
__BRA__	31	MG	3164209	São Romão
__BRA__	31	MG	3164308	São Roque de Minas
__BRA__	31	MG	3164407	São Sebastião da Bela Vista
__BRA__	31	MG	3164431	São Sebastião da Vargem Alegre
__BRA__	31	MG	3164472	São Sebastião do Anta
__BRA__	31	MG	3164506	São Sebastião do Maranhão
__BRA__	31	MG	3164605	São Sebastião do Oeste
__BRA__	31	MG	3164704	São Sebastião do Paraíso
__BRA__	31	MG	3164803	São Sebastião do Rio Preto
__BRA__	31	MG	3164902	São Sebastião do Rio Verde
__BRA__	31	MG	3165206	São Thomé das Letras
__BRA__	31	MG	3165008	São Tiago
__BRA__	31	MG	3165107	São Tomás de Aquino
__BRA__	31	MG	3165305	São Vicente de Minas
__BRA__	31	MG	3165404	Sapucaí-Mirim
__BRA__	31	MG	3165503	Sardoá
__BRA__	31	MG	3165537	Sarzedo
__BRA__	31	MG	3165560	Sem-Peixe
__BRA__	31	MG	3165578	Senador Amaral
__BRA__	31	MG	3165602	Senador Cortes
__BRA__	31	MG	3165701	Senador Firmino
__BRA__	31	MG	3165800	Senador José Bento
__BRA__	31	MG	3165909	Senador Modestino Gonçalves
__BRA__	31	MG	3166006	Senhora de Oliveira
__BRA__	31	MG	3166105	Senhora do Porto
__BRA__	31	MG	3166204	Senhora dos Remédios
__BRA__	31	MG	3166303	Sericita
__BRA__	31	MG	3166402	Seritinga
__BRA__	31	MG	3166501	Serra Azul de Minas
__BRA__	31	MG	3166600	Serra da Saudade
__BRA__	31	MG	3166808	Serra do Salitre
__BRA__	31	MG	3166709	Serra dos Aimorés
__BRA__	31	MG	3166907	Serrania
__BRA__	31	MG	3166956	Serranópolis de Minas
__BRA__	31	MG	3167004	Serranos
__BRA__	31	MG	3167103	Serro
__BRA__	31	MG	3167202	Sete Lagoas
__BRA__	31	MG	3165552	Setubinha
__BRA__	31	MG	3167301	Silveirânia
__BRA__	31	MG	3167400	Silvianópolis
__BRA__	31	MG	3167509	Simão Pereira
__BRA__	31	MG	3167608	Simonésia
__BRA__	31	MG	3167707	Sobrália
__BRA__	31	MG	3167806	Soledade de Minas
__BRA__	31	MG	3167905	Tabuleiro
__BRA__	31	MG	3168002	Taiobeiras
__BRA__	31	MG	3168051	Taparuba
__BRA__	31	MG	3168101	Tapira
__BRA__	31	MG	3168200	Tapiraí
__BRA__	31	MG	3168309	Taquaraçu de Minas
__BRA__	31	MG	3168408	Tarumirim
__BRA__	31	MG	3168507	Teixeiras
__BRA__	31	MG	3168606	Teófilo Otoni
__BRA__	31	MG	3168705	Timóteo
__BRA__	31	MG	3168804	Tiradentes
__BRA__	31	MG	3168903	Tiros
__BRA__	31	MG	3169000	Tocantins
__BRA__	31	MG	3169059	Tocos do Moji
__BRA__	31	MG	3169109	Toledo
__BRA__	31	MG	3169208	Tombos
__BRA__	31	MG	3169307	Três Corações
__BRA__	31	MG	3169356	Três Marias
__BRA__	31	MG	3169406	Três Pontas
__BRA__	31	MG	3169505	Tumiritinga
__BRA__	31	MG	3169604	Tupaciguara
__BRA__	31	MG	3169703	Turmalina
__BRA__	31	MG	3169802	Turvolândia
__BRA__	31	MG	3169901	Ubá
__BRA__	31	MG	3170008	Ubaí
__BRA__	31	MG	3170057	Ubaporanga
__BRA__	31	MG	3170107	Uberaba
__BRA__	31	MG	3170206	Uberlândia
__BRA__	31	MG	3170305	Umburatiba
__BRA__	31	MG	3170404	Unaí
__BRA__	31	MG	3170438	União de Minas
__BRA__	31	MG	3170479	Uruana de Minas
__BRA__	31	MG	3170503	Urucânia
__BRA__	31	MG	3170529	Urucuia
__BRA__	31	MG	3170578	Vargem Alegre
__BRA__	31	MG	3170602	Vargem Bonita
__BRA__	31	MG	3170651	Vargem Grande do Rio Pardo
__BRA__	31	MG	3170701	Varginha
__BRA__	31	MG	3170750	Varjão de Minas
__BRA__	31	MG	3170800	Várzea da Palma
__BRA__	31	MG	3170909	Varzelândia
__BRA__	31	MG	3171006	Vazante
__BRA__	31	MG	3171030	Verdelândia
__BRA__	31	MG	3171071	Veredinha
__BRA__	31	MG	3171105	Veríssimo
__BRA__	31	MG	3171154	Vermelho Novo
__BRA__	31	MG	3171204	Vespasiano
__BRA__	31	MG	3171303	Viçosa
__BRA__	31	MG	3171402	Vieiras
__BRA__	31	MG	3171600	Virgem da Lapa
__BRA__	31	MG	3171709	Virgínia
__BRA__	31	MG	3171808	Virginópolis
__BRA__	31	MG	3171907	Virgolândia
__BRA__	31	MG	3172004	Visconde do Rio Branco
__BRA__	31	MG	3172103	Volta Grande
__BRA__	31	MG	3172202	Wenceslau Braz
\.
