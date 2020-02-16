
CREATE TABLE public.account (
    id integer NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL
);

CREATE TABLE public.book (
    id integer NOT NULL,
    isbn character varying,
    title character varying,
    author character varying,
    year character varying
);

CREATE TABLE public.review (
    id integer NOT NULL,
    user_id integer NOT NULL,
    book_id integer NOT NULL,
    score numeric NOT NULL,
    comment character varying,
    create_date date NOT NULL
);
