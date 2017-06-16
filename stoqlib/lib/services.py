# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2017 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from collections import OrderedDict

# Lista de serviços anexa à Lei Complementar nº 116, de 31 de julho de 2003.


SERVICE_LIST = OrderedDict([
    ("1.01", "Análise e desenvolvimento de sistemas."),  # nopep8
    ("1.02", "Programação."),  # nopep8
    ("1.03", "Processamento de dados e congêneres."),  # nopep8
    ("1.04", "Elaboração de programas de computadores, inclusive de jogos eletrônicos."),  # nopep8
    ("1.03", "Processamento, armazenamento ou hospedagem de dados, textos, imagens, vídeos, páginas eletrônicas, aplicativos e sistemas de informação, entre outros formatos, e congêneres."),  # nopep8
    ("1.04", "Elaboração de programas de computadores, inclusive de jogos eletrônicos, independentemente da arquitetura construtiva da máquina em que o programa será executado, incluindo tablets, smartphones e congêneres."),  # nopep8
    ("1.05", "Licenciamento ou cessão de direito de uso de programas de computação."),  # nopep8
    ("1.06", "Assessoria e consultoria em informática."),  # nopep8
    ("1.07", "Suporte técnico em informática, inclusive instalação, configuração e manutenção de programas de computação e bancos de dados."),  # nopep8
    ("1.08", "Planejamento, confecção, manutenção e atualização de páginas eletrônicas."),  # nopep8
    ("1.09", "Disponibilização, sem cessão definitiva, de conteúdos de áudio, vídeo, imagem e texto por meio da internet, respeitada a imunidade de livros, jornais e periódicos (exceto a distribuição de conteúdos pelas prestadoras de Serviço de Acesso Condicionado"),  # nopep8
    ("2.01", "Serviços de pesquisas e desenvolvimento de qualquer natureza."),  # nopep8
    ("3.01", "(VETADO)"),  # nopep8
    ("3.02", "Cessão de direito de uso de marcas e de sinais de propaganda."),  # nopep8
    ("3.03", "Exploração de salões de festas, centro de convenções, escritórios virtuais, stands, quadras esportivas, estádios, ginásios, auditórios, casas de espetáculos, parques de diversões, canchas e congêneres, para realização de eventos ou negócios de qualquer natureza."),  # nopep8
    ("3.04", "Locação, sublocação, arrendamento, direito de passagem ou permissão de uso, compartilhado ou não, de ferrovia, rodovia, postes, cabos, dutos e condutos de qualquer natureza."),  # nopep8
    ("3.05", "Cessão de andaimes, palcos, coberturas e outras estruturas de uso temporário."),  # nopep8
    ("4.01", "Medicina e biomedicina."),  # nopep8
    ("4.02", "Análises clínicas, patologia, eletricidade médica, radioterapia, quimioterapia, ultra-sonografia, ressonância magnética, radiologia, tomografia e congêneres."),  # nopep8
    ("4.03", "Hospitais, clínicas, laboratórios, sanatórios, manicômios, casas de saúde, prontos-socorros, ambulatórios e congêneres."),  # nopep8
    ("4.04", "Instrumentação cirúrgica."),  # nopep8
    ("4.05", "Acupuntura."),  # nopep8
    ("4.06", "Enfermagem, inclusive serviços auxiliares."),  # nopep8
    ("4.07", "Serviços farmacêuticos."),  # nopep8
    ("4.08", "Terapia ocupacional, fisioterapia e fonoaudiologia."),  # nopep8
    ("4.09", "Terapias de qualquer espécie destinadas ao tratamento físico, orgânico e mental."),  # nopep8
    ("4.10", "Nutrição."),  # nopep8
    ("4.11", "Obstetrícia."),  # nopep8
    ("4.12", "Odontologia."),  # nopep8
    ("4.13", "Ortóptica."),  # nopep8
    ("4.14", "Próteses sob encomenda."),  # nopep8
    ("4.15", "Psicanálise."),  # nopep8
    ("4.16", "Psicologia."),  # nopep8
    ("4.17", "Casas de repouso e de recuperação, creches, asilos e congêneres."),  # nopep8
    ("4.18", "Inseminação artificial, fertilização in vitro e congêneres."),  # nopep8
    ("4.19", "Bancos de sangue, leite, pele, olhos, óvulos, sêmen e congêneres."),  # nopep8
    ("4.20", "Coleta de sangue, leite, tecidos, sêmen, órgãos e materiais biológicos de qualquer espécie."),  # nopep8
    ("4.21", "Unidade de atendimento, assistência ou tratamento móvel e congêneres."),  # nopep8
    ("4.22", "Planos de medicina de grupo ou individual e convênios para prestação de assistência médica, hospitalar, odontológica e congêneres."),  # nopep8
    ("4.23", "Outros planos de saúde que se cumpram através de serviços de terceiros contratados, credenciados, cooperados ou apenas pagos pelo operador do plano mediante indicação do beneficiário."),  # nopep8
    ("5.01", "Medicina veterinária e zootecnia."),  # nopep8
    ("5.02", "Hospitais, clínicas, ambulatórios, prontos-socorros e congêneres, na área veterinária."),  # nopep8
    ("5.03", "Laboratórios de análise na área veterinária."),  # nopep8
    ("5.04", "Inseminação artificial, fertilização in vitro e congêneres."),  # nopep8
    ("5.05", "Bancos de sangue e de órgãos e congêneres."),  # nopep8
    ("5.06", "Coleta de sangue, leite, tecidos, sêmen, órgãos e materiais biológicos de qualquer espécie."),  # nopep8
    ("5.07", "Unidade de atendimento, assistência ou tratamento móvel e congêneres."),  # nopep8
    ("5.08", "Guarda, tratamento, amestramento, embelezamento, alojamento e congêneres."),  # nopep8
    ("5.09", "Planos de atendimento e assistência médico-veterinária."),  # nopep8
    ("6.01", "Barbearia, cabeleireiros, manicuros, pedicuros e congêneres."),  # nopep8
    ("6.02", "Esteticistas, tratamento de pele, depilação e congêneres."),  # nopep8
    ("6.03", "Banhos, duchas, sauna, massagens e congêneres."),  # nopep8
    ("6.04", "Ginástica, dança, esportes, natação, artes marciais e demais atividades físicas."),  # nopep8
    ("6.05", "Centros de emagrecimento, spa e congêneres."),  # nopep8
    ("6.06", "Aplicação de tatuagens, piercings e congêneres."),  # nopep8
    ("7.01", "Engenharia, agronomia, agrimensura, arquitetura, geologia, urbanismo, paisagismo e congêneres."),  # nopep8
    ("7.02", "Execução, por administração, empreitada ou subempreitada, de obras de construção civil, hidráulica ou elétrica e de outras obras semelhantes, inclusive sondagem, perfuração de poços, escavação, drenagem e irrigação, terraplanagem, pavimentação, concretagem e a instalação e montagem de produtos, peças e equipamentos (exceto o fornecimento de mercadorias produzidas pelo prestador de serviços fora do local da prestação dos serviços, que fica sujeito ao ICMS)."),  # nopep8
    ("7.03", "Elaboração de planos diretores, estudos de viabilidade, estudos organizacionais e outros, relacionados com obras e serviços de engenharia; elaboração de anteprojetos, projetos básicos e projetos executivos para trabalhos de engenharia."),  # nopep8
    ("7.04", "Demolição."),  # nopep8
    ("7.05", "Reparação, conservação e reforma de edifícios, estradas, pontes, portos e congêneres (exceto o fornecimento de mercadorias produzidas pelo prestador dos serviços, fora do local da prestação dos serviços, que fica sujeito ao ICMS)."),  # nopep8
    ("7.06", "Colocação e instalação de tapetes, carpetes, assoalhos, cortinas, revestimentos de parede, vidros, divisórias, placas de gesso e congêneres, com material fornecido pelo tomador do serviço."),  # nopep8
    ("7.07", "Recuperação, raspagem, polimento e lustração de pisos e congêneres."),  # nopep8
    ("7.08", "Calafetação."),  # nopep8
    ("7.09", "Varrição, coleta, remoção, incineração, tratamento, reciclagem, separação e destinação final de lixo, rejeitos e outros resíduos quaisquer."),  # nopep8
    ("7.10", "Limpeza, manutenção e conservação de vias e logradouros públicos, imóveis, chaminés, piscinas, parques, jardins e congêneres."),  # nopep8
    ("7.11", "Decoração e jardinagem, inclusive corte e poda de árvores."),  # nopep8
    ("7.12", "Controle e tratamento de efluentes de qualquer natureza e de agentes físicos, químicos e biológicos."),  # nopep8
    ("7.13", "Dedetização, desinfecção, desinsetização, imunização, higienização, desratização, pulverização e congêneres."),  # nopep8
    ("7.14", "(VETADO)"),  # nopep8
    ("7.15", "(VETADO)"),  # nopep8
    ("7.16", "Florestamento, reflorestamento, semeadura, adubação e congêneres."),  # nopep8
    ("7.16", "Florestamento, reflorestamento, semeadura, adubação, reparação de solo, plantio, silagem, colheita, corte e descascamento de árvores, silvicultura, exploração florestal e dos serviços congêneres indissociáveis da formação, manutenção e colheita de florestas, para quaisquer fins e por quaisquer meios."),  # nopep8
    ("7.17", "Escoramento, contenção de encostas e serviços congêneres."),  # nopep8
    ("7.18", "Limpeza e dragagem de rios, portos, canais, baías, lagos, lagoas, represas, açudes e congêneres."),  # nopep8
    ("7.19", "Acompanhamento e fiscalização da execução de obras de engenharia, arquitetura e urbanismo."),  # nopep8
    ("7.20", "Aerofotogrametria (inclusive interpretação), cartografia, mapeamento, levantamentos topográficos, batimétricos, geográficos, geodésicos, geológicos, geofísicos e congêneres."),  # nopep8
    ("7.21", "Pesquisa, perfuração, cimentação, mergulho, perfilagem, concretação, testemunhagem, pescaria, estimulação e outros serviços relacionados com a exploração e explotação de petróleo, gás natural e de outros recursos minerais."),  # nopep8
    ("7.22", "Nucleação e bombardeamento de nuvens e congêneres."),  # nopep8
    ("8.01", "Ensino regular pré-escolar, fundamental, médio e superior."),  # nopep8
    ("8.02", "Instrução, treinamento, orientação pedagógica e educacional, avaliação de conhecimentos de qualquer natureza."),  # nopep8
    ("9.01", "Hospedagem de qualquer natureza em hotéis, apart-service condominiais, flat, apart-hotéis, hotéis residência, residence-service, suite service, hotelaria marítima, motéis, pensões e congêneres; ocupação por temporada com fornecimento de serviço (o valor da alimentação e gorjeta, quando incluído no preço da diária, fica sujeito ao Imposto Sobre Serviços)."),  # nopep8
    ("9.02", "Agenciamento, organização, promoção, intermediação e execução de programas de turismo, passeios, viagens, excursões, hospedagens e congêneres."),  # nopep8
    ("9.03", "Guias de turismo."),  # nopep8
    ("10.01", "Agenciamento, corretagem ou intermediação de câmbio, de seguros, de cartões de crédito, de planos de saúde e de planos de previdência privada."),  # nopep8
    ("10.02", "Agenciamento, corretagem ou intermediação de títulos em geral, valores mobiliários e contratos quaisquer."),  # nopep8
    ("10.03", "Agenciamento, corretagem ou intermediação de direitos de propriedade industrial, artística ou literária."),  # nopep8
    ("10.04", "Agenciamento, corretagem ou intermediação de contratos de arrendamento mercantil (leasing), de franquia (franchising) e de faturização (factoring)."),  # nopep8
    ("10.05", "Agenciamento, corretagem ou intermediação de bens móveis ou imóveis, não abrangidos em outros itens ou subitens, inclusive aqueles realizados no âmbito de Bolsas de Mercadorias e Futuros, por quaisquer meios."),  # nopep8
    ("10.06", "Agenciamento marítimo."),  # nopep8
    ("10.07", "Agenciamento de notícias."),  # nopep8
    ("10.08", "Agenciamento de publicidade e propaganda, inclusive o agenciamento de veiculação por quaisquer meios."),  # nopep8
    ("10.09", "Representação de qualquer natureza, inclusive comercial."),  # nopep8
    ("10.10", "Distribuição de bens de terceiros."),  # nopep8
    ("11.01", "Guarda e estacionamento de veículos terrestres automotores, de aeronaves e de embarcações."),  # nopep8
    ("11.02", "Vigilância, segurança ou monitoramento de bens e pessoas."),  # nopep8
    ("11.02", "Vigilância, segurança ou monitoramento de bens, pessoas e semoventes."),  # nopep8
    ("11.03", "Escolta, inclusive de veículos e cargas."),  # nopep8
    ("11.04", "Armazenamento, depósito, carga, descarga, arrumação e guarda de bens de qualquer espécie."),  # nopep8
    ("12.01", "Espetáculos teatrais."),  # nopep8
    ("12.02", "Exibições cinematográficas."),  # nopep8
    ("12.03", "Espetáculos circenses."),  # nopep8
    ("12.04", "Programas de auditório."),  # nopep8
    ("12.05", "Parques de diversões, centros de lazer e congêneres."),  # nopep8
    ("12.06", "Boates, taxi-dancing e congêneres."),  # nopep8
    ("12.07", "Shows, ballet, danças, desfiles, bailes, óperas, concertos, recitais, festivais e congêneres."),  # nopep8
    ("12.08", "Feiras, exposições, congressos e congêneres."),  # nopep8
    ("12.09", "Bilhares, boliches e diversões eletrônicas ou não."),  # nopep8
    ("12.10", "Corridas e competições de animais."),  # nopep8
    ("12.11", "Competições esportivas ou de destreza física ou intelectual, com ou sem a participação do espectador."),  # nopep8
    ("12.12", "Execução de música."),  # nopep8
    ("12.13", "Produção, mediante ou sem encomenda prévia, de eventos, espetáculos, entrevistas, shows, ballet, danças, desfiles, bailes, teatros, óperas, concertos, recitais, festivais e congêneres."),  # nopep8
    ("12.14", "Fornecimento de música para ambientes fechados ou não, mediante transmissão por qualquer processo."),  # nopep8
    ("12.15", "Desfiles de blocos carnavalescos ou folclóricos, trios elétricos e congêneres."),  # nopep8
    ("12.16", "Exibição de filmes, entrevistas, musicais, espetáculos, shows, concertos, desfiles, óperas, competições esportivas, de destreza intelectual ou congêneres."),  # nopep8
    ("12.17", "Recreação e animação, inclusive em festas e eventos de qualquer natureza."),  # nopep8
    ("13.01", "(VETADO)"),  # nopep8
    ("13.02", "Fonografia ou gravação de sons, inclusive trucagem, dublagem, mixagem e congêneres."),  # nopep8
    ("13.03", "Fotografia e cinematografia, inclusive revelação, ampliação, cópia, reprodução, trucagem e congêneres."),  # nopep8
    ("13.04", "Reprografia, microfilmagem e digitalização."),  # nopep8
    ("13.05", "Composição gráfica, fotocomposição, clicheria, zincografia, litografia, fotolitografia."),  # nopep8
    ("13.05", "Composição gráfica, inclusive confecção de impressos gráficos, fotocomposição, clicheria, zincografia, litografia e fotolitografia, exceto se destinados a posterior operação de comercialização ou industrialização, ainda que incorporados, de qualquer forma, a outra mercadoria que deva ser objeto de posterior circulação, tais como bulas, rótulos, etiquetas, caixas, cartuchos, embalagens e manuais técnicos e de instrução, quando ficarão sujeitos ao ICMS."),  # nopep8
    ("14.01", "Lubrificação, limpeza, lustração, revisão, carga e recarga, conserto, restauração, blindagem, manutenção e conservação de máquinas, veículos, aparelhos, equipamentos, motores, elevadores ou de qualquer objeto (exceto peças e partes empregadas, que ficam sujeitas ao ICMS)."),  # nopep8
    ("14.02", "Assistência técnica."),  # nopep8
    ("14.03", "Recondicionamento de motores (exceto peças e partes empregadas, que ficam sujeitas ao ICMS)."),  # nopep8
    ("14.04", "Recauchutagem ou regeneração de pneus."),  # nopep8
    ("14.05", "Restauração, recondicionamento, acondicionamento, pintura, beneficiamento, lavagem, secagem, tingimento, galvanoplastia, anodização, corte, recorte, polimento, plastificação e congêneres, de objetos quaisquer."),  # nopep8
    ("14.05", "Restauração, recondicionamento, acondicionamento, pintura, beneficiamento, lavagem, secagem, tingimento, galvanoplastia, anodização, corte, recorte, plastificação, costura, acabamento, polimento e congêneres de objetos quaisquer."),  # nopep8
    ("14.06", "Instalação e montagem de aparelhos, máquinas e equipamentos, inclusive montagem industrial, prestados ao usuário final, exclusivamente com material por ele fornecido."),  # nopep8
    ("14.07", "Colocação de molduras e congêneres."),  # nopep8
    ("14.08", "Encadernação, gravação e douração de livros, revistas e congêneres."),  # nopep8
    ("14.09", "Alfaiataria e costura, quando o material for fornecido pelo usuário final, exceto aviamento."),  # nopep8
    ("14.10", "Tinturaria e lavanderia."),  # nopep8
    ("14.11", "Tapeçaria e reforma de estofamentos em geral."),  # nopep8
    ("14.12", "Funilaria e lanternagem."),  # nopep8
    ("14.13", "Carpintaria e serralheria."),  # nopep8
    ("14.14", "Guincho intramunicipal, guindaste e içamento."),  # nopep8
    ("15.01", "Administração de fundos quaisquer, de consórcio, de cartão de crédito ou débito e congêneres, de carteira de clientes, de cheques pré-datados e congêneres."),  # nopep8
    ("15.02", "Abertura de contas em geral, inclusive conta-corrente, conta de investimentos e aplicação e caderneta de poupança, no País e no exterior, bem como a manutenção das referidas contas ativas e inativas."),  # nopep8
    ("15.03", "Locação e manutenção de cofres particulares, de terminais eletrônicos, de terminais de atendimento e de bens e equipamentos em geral."),  # nopep8
    ("15.04", "Fornecimento ou emissão de atestados em geral, inclusive atestado de idoneidade, atestado de capacidade financeira e congêneres."),  # nopep8
    ("15.05", "Cadastro, elaboração de ficha cadastral, renovação cadastral e congêneres, inclusão ou exclusão no Cadastro de Emitentes de Cheques sem Fundos – CCF ou em quaisquer outros bancos cadastrais."),  # nopep8
    ("15.06", "Emissão, reemissão e fornecimento de avisos, comprovantes e documentos em geral; abono de firmas; coleta e entrega de documentos, bens e valores; comunicação com outra agência ou com a administração central; licenciamento eletrônico de veículos; transferência de veículos; agenciamento fiduciário ou depositário; devolução de bens em custódia."),  # nopep8
    ("15.07", "Acesso, movimentação, atendimento e consulta a contas em geral, por qualquer meio ou processo, inclusive por telefone, fac-símile, internet e telex, acesso a terminais de atendimento, inclusive vinte e quatro horas; acesso a outro banco e a rede compartilhada; fornecimento de saldo, extrato e demais informações relativas a contas em geral, por qualquer meio ou processo."),  # nopep8
    ("15.08", "Emissão, reemissão, alteração, cessão, substituição, cancelamento e registro de contrato de crédito; estudo, análise e avaliação de operações de crédito; emissão, concessão, alteração ou contratação de aval, fiança, anuência e congêneres; serviços relativos a abertura de crédito, para quaisquer fins."),  # nopep8
    ("15.09", "Arrendamento mercantil (leasing) de quaisquer bens, inclusive cessão de direitos e obrigações, substituição de garantia, alteração, cancelamento e registro de contrato, e demais serviços relacionados ao arrendamento mercantil (leasing)."),  # nopep8
    ("15.10", "Serviços relacionados a cobranças, recebimentos ou pagamentos em geral, de títulos quaisquer, de contas ou carnês, de câmbio, de tributos e por conta de terceiros, inclusive os efetuados por meio eletrônico, automático ou por máquinas de atendimento; fornecimento de posição de cobrança, recebimento ou pagamento; emissão de carnês, fichas de compensação, impressos e documentos em geral."),  # nopep8
    ("15.11", "Devolução de títulos, protesto de títulos, sustação de protesto, manutenção de títulos, reapresentação de títulos, e demais serviços a eles relacionados."),  # nopep8
    ("15.12", "Custódia em geral, inclusive de títulos e valores mobiliários."),  # nopep8
    ("15.13", "Serviços relacionados a operações de câmbio em geral, edição, alteração, prorrogação, cancelamento e baixa de contrato de câmbio; emissão de registro de exportação ou de crédito; cobrança ou depósito no exterior; emissão, fornecimento e cancelamento de cheques de viagem; fornecimento, transferência, cancelamento e demais serviços relativos a carta de crédito de importação, exportação e garantias recebidas; envio e recebimento de mensagens em geral relacionadas a operações de câmbio."),  # nopep8
    ("15.14", "Fornecimento, emissão, reemissão, renovação e manutenção de cartão magnético, cartão de crédito, cartão de débito, cartão salário e congêneres."),  # nopep8
    ("15.15", "Compensação de cheques e títulos quaisquer; serviços relacionados a depósito, inclusive depósito identificado, a saque de contas quaisquer, por qualquer meio ou processo, inclusive em terminais eletrônicos e de atendimento."),  # nopep8
    ("15.16", "Emissão, reemissão, liquidação, alteração, cancelamento e baixa de ordens de pagamento, ordens de crédito e similares, por qualquer meio ou processo; serviços relacionados à transferência de valores, dados, fundos, pagamentos e similares, inclusive entre contas em geral."),  # nopep8
    ("15.17", "Emissão, fornecimento, devolução, sustação, cancelamento e oposição de cheques quaisquer, avulso ou por talão."),  # nopep8
    ("15.18", "Serviços relacionados a crédito imobiliário, avaliação e vistoria de imóvel ou obra, análise técnica e jurídica, emissão, reemissão, alteração, transferência e renegociação de contrato, emissão e reemissão do termo de quitação e demais serviços relacionados a crédito imobiliário."),  # nopep8
    ("16.01", "Serviços de transporte de natureza municipal."),  # nopep8
    ("16.01", "Serviços de transporte coletivo municipal rodoviário, metroviário, ferroviário e aquaviário de passageiros."),  # nopep8
    ("16.02", "Outros serviços de transporte de natureza municipal."),  # nopep8
    ("17.01", "Assessoria ou consultoria de qualquer natureza, não contida em outros itens desta lista; análise, exame, pesquisa, coleta, compilação e fornecimento de dados e informações de qualquer natureza, inclusive cadastro e similares."),  # nopep8
    ("17.02", "Datilografia, digitação, estenografia, expediente, secretaria em geral, resposta audível, redação, edição, interpretação, revisão, tradução, apoio e infra-estrutura administrativa e congêneres."),  # nopep8
    ("17.03", "Planejamento, coordenação, programação ou organização técnica, financeira ou administrativa."),  # nopep8
    ("17.04", "Recrutamento, agenciamento, seleção e colocação de mão-de-obra."),  # nopep8
    ("17.05", "Fornecimento de mão-de-obra, mesmo em caráter temporário, inclusive de empregados ou trabalhadores, avulsos ou temporários, contratados pelo prestador de serviço."),  # nopep8
    ("17.06", "Propaganda e publicidade, inclusive promoção de vendas, planejamento de campanhas ou sistemas de publicidade, elaboração de desenhos, textos e demais materiais publicitários."),  # nopep8
    ("17.07", "(VETADO)"),  # nopep8
    ("17.08", "Franquia (franchising)."),  # nopep8
    ("17.09", "Perícias, laudos, exames técnicos e análises técnicas."),  # nopep8
    ("17.10", "Planejamento, organização e administração de feiras, exposições, congressos e congêneres."),  # nopep8
    ("17.11", "Organização de festas e recepções; bufê (exceto o fornecimento de alimentação e bebidas, que fica sujeito ao ICMS)."),  # nopep8
    ("17.12", "Administração em geral, inclusive de bens e negócios de terceiros."),  # nopep8
    ("17.13", "Leilão e congêneres."),  # nopep8
    ("17.14", "Advocacia."),  # nopep8
    ("17.15", "Arbitragem de qualquer espécie, inclusive jurídica."),  # nopep8
    ("17.16", "Auditoria."),  # nopep8
    ("17.17", "Análise de Organização e Métodos."),  # nopep8
    ("17.18", "Atuária e cálculos técnicos de qualquer natureza."),  # nopep8
    ("17.19", "Contabilidade, inclusive serviços técnicos e auxiliares."),  # nopep8
    ("17.20", "Consultoria e assessoria econômica ou financeira."),  # nopep8
    ("17.21", "Estatística."),  # nopep8
    ("17.22", "Cobrança em geral."),  # nopep8
    ("17.23", "Assessoria, análise, avaliação, atendimento, consulta, cadastro, seleção, gerenciamento de informações, administração de contas a receber ou a pagar e em geral, relacionados a operações de faturização (factoring)."),  # nopep8
    ("17.24", "Apresentação de palestras, conferências, seminários e congêneres."),  # nopep8
    ("17.25", "Inserção de textos, desenhos e outros materiais de propaganda e publicidade, em qualquer meio (exceto em livros, jornais, periódicos e nas modalidades de serviços de radiodifusão sonora e de sons e imagens de recepção livre e gratuita)."),  # nopep8
    ("18.01", "Serviços de regulação de sinistros vinculados a contratos de seguros; inspeção e avaliação de riscos para cobertura de contratos de seguros; prevenção e gerência de riscos seguráveis e congêneres."),  # nopep8
    ("19.01", "Serviços de distribuição e venda de bilhetes e demais produtos de loteria, bingos, cartões, pules ou cupons de apostas, sorteios, prêmios, inclusive os decorrentes de títulos de capitalização e congêneres."),  # nopep8
    ("20.01", "Serviços portuários, ferroportuários, utilização de porto, movimentação de passageiros, reboque de embarcações, rebocador escoteiro, atracação, desatracação, serviços de praticagem, capatazia, armazenagem de qualquer natureza, serviços acessórios, movimentação de mercadorias, serviços de apoio marítimo, de movimentação ao largo, serviços de armadores, estiva, conferência, logística e congêneres."),  # nopep8
    ("20.02", "Serviços aeroportuários, utilização de aeroporto, movimentação de passageiros, armazenagem de qualquer natureza, capatazia, movimentação de aeronaves, serviços de apoio aeroportuários, serviços acessórios, movimentação de mercadorias, logística e congêneres."),  # nopep8
    ("20.03", "Serviços de terminais rodoviários, ferroviários, metroviários, movimentação de passageiros, mercadorias, inclusive     suas operações, logística e congêneres."),  # nopep8
    ("21.01", "Serviços de registros públicos, cartorários e notariais."),  # nopep8
    ("22.01", "Serviços de exploração de rodovia mediante cobrança de preço ou pedágio dos usuários, envolvendo execução de serviços de conservação, manutenção, melhoramentos para adequação de capacidade e segurança de trânsito, operação, monitoração, assistência aos usuários e outros serviços definidos em contratos, atos de concessão ou de permissão ou em      normas oficiais."),  # nopep8
    ("23.01", "Serviços de programação e comunicação visual, desenho industrial e congêneres."),  # nopep8
    ("24.01", "Serviços de chaveiros, confecção de carimbos, placas, sinalização visual, banners, adesivos e congêneres."),  # nopep8
    ("25.01", "Funerais, inclusive fornecimento de caixão, urna ou esquifes; aluguel de capela; transporte do corpo cadavérico; fornecimento de flores, coroas e outros paramentos; desembaraço de certidão de óbito; fornecimento de véu, essa e outros adornos; embalsamento, embelezamento, conservação ou restauração de cadáveres."),  # nopep8
    ("25.02", "Cremação de corpos e partes de corpos cadavéricos."),  # nopep8
    ("25.02", "Translado intramunicipal e cremação de corpos e partes de corpos cadavéricos."),  # nopep8
    ("25.03", "Planos ou convênio funerários."),  # nopep8
    ("25.04", "Manutenção e conservação de jazigos e cemitérios."),  # nopep8
    ("25.05", "Cessão de uso de espaços em cemitérios para sepultamento."),  # nopep8
    ("26.01", "Serviços de coleta, remessa ou entrega de correspondências, documentos, objetos, bens ou valores, inclusive pelos correios e suas agências franqueadas; courrier e congêneres."),  # nopep8
    ("27.01", "Serviços de assistência social."),  # nopep8
    ("28.01", "Serviços de avaliação de bens e serviços de qualquer natureza."),  # nopep8
    ("29.01", "Serviços de biblioteconomia."),  # nopep8
    ("30.01", "Serviços de biologia, biotecnologia e química."),  # nopep8
    ("31.01", "Serviços técnicos em edificações, eletrônica, eletrotécnica, mecânica, telecomunicações e congêneres."),  # nopep8
    ("32.01", "Serviços de desenhos técnicos."),  # nopep8
    ("33.01", "Serviços de desembaraço aduaneiro, comissários, despachantes e congêneres."),  # nopep8
    ("34.01", "Serviços de investigações particulares, detetives e congêneres."),  # nopep8
    ("35.01", "Serviços de reportagem, assessoria de imprensa, jornalismo e relações públicas."),  # nopep8
    ("36.01", "Serviços de meteorologia."),  # nopep8
    ("37.01", "Serviços de artistas, atletas, modelos e manequins."),  # nopep8
    ("38.01", "Serviços de museologia."),  # nopep8
    ("39.01", "Serviços de ourivesaria e lapidação (quando o material for fornecido pelo tomador do serviço)."),  # nopep8
    ("40.01", "Obras de arte sob encomenda."),  # nopep8
])
