--
-- Copyright (C) 2012 Async Open Source
--
-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU Lesser General Public License
-- as published by the Free Software Foundation; either version 2
-- of the License, or (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program; if not, write to the Free Software
-- Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
--
--
-- Author(s): Stoq Team <stoq-devel@async.com.br>
--

--
-- Stoq SQL function library
--
-- This needs to work in PostgreSQL 8.4.

--
-- Source: http://wiki.postgresql.org/wiki/CREATE_OR_REPLACE_LANGUAGE
-- Author: David Fetter
--

CREATE OR REPLACE FUNCTION stoq_create_language_plpgsql()
RETURNS VOID
LANGUAGE SQL
AS $$
CREATE LANGUAGE plpgsql;
$$;

SELECT
    CASE
    WHEN EXISTS(
        SELECT 1
        FROM pg_catalog.pg_language
        WHERE lanname = 'plpgsql'
    )
    THEN NULL
    ELSE stoq_create_language_plpgsql() END;

DROP FUNCTION stoq_create_language_plpgsql();


--
-- This is used to remove accents from a string
--
-- Source: http://wiki.postgresql.org/wiki/Strip_accents_from_strings,_and_output_in_lowercase
-- Author: Thom Brown
--
-- Source: http://lehelk.com/2011/05/06/script-to-remove-diacritics/
--

CREATE OR REPLACE FUNCTION stoq_normalize_string(text) RETURNS text AS $$
DECLARE
    input_string text := $1;
BEGIN

input_string := LOWER(input_string);

-- These are the must common cases for latin based charceter sets
input_string := translate(input_string, 'ẚàáâầấẫẩãāăằắẵẳȧǡäǟảåǻǎȁȃạậặḁąⱥɐ',
                                        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
input_string := translate(input_string, 'èéêềếễểẽēḕḗĕėëẻěȅȇẹệȩḝęḙḛɇɛǝ',
                                        'eeeeeeeeeeeeeeeeeeeeeeeeeeee');
input_string := translate(input_string, 'ìíîĩīĭïḯỉǐȉȋịįḭɨı',
                                        'iiiiiiiiiiiiiiiii');
input_string := translate(input_string, 'òóôồốỗổõṍȭṏōṑṓŏȯȱöȫỏőǒȍȏơờớỡởợọộǫǭøǿɔꝋꝍɵ',
                                        'oooooooooooooooooooooooooooooooooooooooo');
input_string := translate(input_string, 'ùúûũṹūṻŭüǜǘǖǚủůűǔȕȗưừứữửựụṳųṷṵʉ',
                                        'uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu');
input_string := translate(input_string, 'çñ',
                                        'cn');

-- Not putting those characteres to avoid extra overhead
--input_string := translate(input_string, 'ḃḅḇƀƃɓ', 'bbbbbb');
--input_string := translate(input_string, 'ćĉċčçḉƈȼꜿↄ', 'cccccccccc');
--input_string := translate(input_string, 'ḋďḍḑḓḏđƌɖɗꝺ', 'ddddddddddd');
--input_string := translate(input_string, 'ḟƒꝼ', 'fff');
--input_string := translate(input_string, 'ǵĝḡğġǧģǥɠᵹꝿ', 'ggggggggggg');
--input_string := translate(input_string, 'ĥḣḧȟḥḩḫẖħⱨⱶɥ', 'hhhhhhhhhhhh');
--input_string := translate(input_string, 'ĵǰɉ', 'jjj');
--input_string := translate(input_string, 'ḱǩḳķḵƙⱪꝁꝃꝅ', 'kkkkkkkkkk');
--input_string := translate(input_string, 'ŀĺľḷḹļḽḻſłƚɫⱡꝉꞁꝇ', 'llllllllllllllll');
--input_string := translate(input_string, 'ḿṁṃɱɯ', 'mmmmm');
--input_string := translate(input_string, 'ǹńñṅňṇņṋṉƞɲŉꞑ', 'nnnnnnnnnnnnn');
--input_string := translate(input_string, 'ṕṗƥᵽꝑꝓ', 'pppppp');
--input_string := translate(input_string, 'ɋꝗ', 'qq');
--input_string := translate(input_string, 'ŕṙřȑȓṛṝŗṟɍɽꞃ', 'rrrrrrrrrrrr');
--input_string := translate(input_string, 'ßśṥŝṡšṧṣṩșşȿꞅẛ', 'ssssssssssssss');
--input_string := translate(input_string, 'ṫẗťṭțţṱṯŧƭʈⱦꞇ', 'ttttttttttttt');
--input_string := translate(input_string, 'ṽṿʋʌ', 'vvvv');
--input_string := translate(input_string, 'ẁẃŵẇẅẘẉⱳ', 'wwwwwwww');
--input_string := translate(input_string, 'ẋẍ', 'xx');
--input_string := translate(input_string, 'ỳýŷỹȳẏÿỷẙỵƴɏỿ', 'yyyyyyyyyyyyy');
--input_string := translate(input_string, 'źẑżžẓẕƶȥɀⱬ', 'zzzzzzzzzz');

return input_string;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
