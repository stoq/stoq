-- Bug 4039 -  Criação de pesquisa e relatório de estoque de produto por
-- custo médio

ALTER TABLE sale_item
    ADD COLUMN average_cost numeric(10,2) DEFAULT 0;
