-- Initial schema for optical stores plugin.

CREATE TABLE optical_medic (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id),
    person_id uuid UNIQUE NOT NULL REFERENCES person(id) ON UPDATE CASCADE,
    crm_number text UNIQUE
);

CREATE TABLE optical_product (
    id uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    product_id uuid UNIQUE NOT NULL REFERENCES product(id) ON UPDATE CASCADE,

    optical_type integer,

    -- glass frames
    gf_glass_type text,
    gf_size text,
    gf_lens_type text,
    gf_color text,

    -- glass lenses
    gl_photosensitive text,
    gl_anti_glare text,
    gl_refraction_index text,
    gl_classification text,
    gl_addition text,
    gl_diameter text,
    gl_height text,
    gl_availability text,

    -- contact lenses
    cl_degree numeric(6,2),
    cl_classification text,
    cl_lens_type text,
    cl_discard text,
    cl_addition text,
    cl_cylindrical numeric(6, 2),
    cl_axis numeric(6, 2),
    cl_color text,
    cl_curvature text
);

CREATE TABLE optical_work_order (
    id uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    work_order_id uuid UNIQUE NOT NULL REFERENCES work_order(id) ON UPDATE CASCADE,
    medic_id uuid REFERENCES optical_medic(id) ON UPDATE CASCADE,
    prescription_date timestamp,
    patient text,

    lens_type integer,

    -- Frame
    -- MVA - Vertical Frame Measure
    -- MHA - Horizontal Frame Measure
    -- MDA - Diagonal Frame Measure
    frame_type integer,
    frame_mva numeric(6, 2) DEFAULT 0,
    frame_mha numeric(6, 2) DEFAULT 0,
    frame_mda numeric(6, 2) DEFAULT 0,
    frame_bridge numeric(6, 2) DEFAULT 0,

    -- left eye
    le_distance_spherical numeric(6, 2) DEFAULT 0,
    le_distance_cylindrical numeric(6, 2) DEFAULT 0,
    le_distance_axis numeric(6, 2) DEFAULT 0,
    le_distance_prism numeric(6, 2) DEFAULT 0,
    le_distance_base numeric(6, 2) DEFAULT 0,
    le_distance_height numeric(6, 2) DEFAULT 0,
    le_distance_pd numeric(6, 2) DEFAULT 0,
    le_addition numeric(6, 2) DEFAULT 0,
    le_near_spherical numeric(6, 2) DEFAULT 0,
    le_near_cylindrical numeric(6, 2) DEFAULT 0,
    le_near_axis numeric(6, 2) DEFAULT 0,
    le_near_pd numeric(6, 2) DEFAULT 0,

    -- right eye
    re_distance_spherical numeric(6, 2) DEFAULT 0,
    re_distance_cylindrical numeric(6, 2) DEFAULT 0,
    re_distance_axis numeric(6, 2) DEFAULT 0,
    re_distance_prism numeric(6, 2) DEFAULT 0,
    re_distance_base numeric(6, 2) DEFAULT 0,
    re_distance_height numeric(6, 2) DEFAULT 0,
    re_distance_pd numeric(6, 2) DEFAULT 0,
    re_addition numeric(6, 2) DEFAULT 0,
    re_near_spherical numeric(6, 2) DEFAULT 0,
    re_near_cylindrical numeric(6, 2) DEFAULT 0,
    re_near_axis numeric(6, 2) DEFAULT 0,
    re_near_pd numeric(6, 2) DEFAULT 0
);

CREATE TABLE optical_patient_history (
    id uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id),
    create_date timestamp NOT NULL,
    client_id uuid NOT NULL REFERENCES client(id) ON UPDATE CASCADE,
    responsible_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,

    -- General questions
    user_type integer DEFAULT 0,
    occupation text DEFAULT '',
    work_environment text DEFAULT '',

    -- First time user
    has_tested text DEFAULT '',
    tested_brand text DEFAULT '',
    eye_irritation text DEFAULT '',
    purpose_of_use text DEFAULT '',
    intended_hour_usage text DEFAULT '',

    -- Second time / Ex user
    previous_brand text DEFAULT '',
    previous_feeling text DEFAULT '',
    cornea_issues text DEFAULT '',
    hours_per_day_usage text DEFAULT '',

    -- Second time user
    user_since text DEFAULT '',
    has_previous_lenses text DEFAULT '',
    previous_lenses_notes text DEFAULT '',

    -- Ex user
    last_use text DEFAULT '',
    stop_reason text DEFAULT '',
    protein_removal text DEFAULT '',
    cleaning_product text DEFAULT '',

    -- Adaptation test
    eye_injury text DEFAULT '',
    recent_pathology text DEFAULT '',
    using_eye_drops text DEFAULT '',
    health_problems text DEFAULT '',
    using_medicament text DEFAULT '',
    family_health_problems text DEFAULT '',
    end_of_day_feeling text DEFAULT '',

    -- Notes
    history_notes text DEFAULT '',
    adaptation_notes text DEFAULT ''
);

CREATE TABLE optical_patient_measures (
    id uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id),
    create_date timestamp NOT NULL,
    client_id uuid NOT NULL REFERENCES client(id) ON UPDATE CASCADE,
    responsible_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,

    dominant_eye integer default 0,

    le_keratometer_horizontal text DEFAULT '',
    le_keratometer_vertical text DEFAULT '',
    le_keratometer_axis text DEFAULT '',

    re_keratometer_horizontal text DEFAULT '',
    re_keratometer_vertical text DEFAULT '',
    re_keratometer_axis text DEFAULT '',

    le_eyebrown text DEFAULT '',
    le_eyelash text DEFAULT '',
    le_conjunctiva text DEFAULT '',
    le_sclerotic text DEFAULT '',
    le_iris_diameter text DEFAULT '',
    le_eyelid text DEFAULT '',
    le_eyelid_opening text DEFAULT '',
    le_cornea text DEFAULT '',
    le_tbut text DEFAULT '',
    le_schirmer text DEFAULT '',

    re_eyebrown text DEFAULT '',
    re_eyelash text DEFAULT '',
    re_conjunctiva text DEFAULT '',
    re_sclerotic text DEFAULT '',
    re_iris_diameter text DEFAULT '',
    re_eyelid text DEFAULT '',
    re_eyelid_opening text DEFAULT '',
    re_cornea text DEFAULT '',
    re_tbut text DEFAULT '',
    re_schirmer text DEFAULT '',

    notes text DEFAULT ''
);

CREATE TABLE optical_patient_test (
    id uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id),
    create_date timestamp NOT NULL,
    client_id uuid NOT NULL REFERENCES client(id) ON UPDATE CASCADE,
    responsible_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,

    le_item text DEFAULT '',
    le_brand text DEFAULT '',
    le_base_curve text DEFAULT '',
    le_spherical_degree text DEFAULT '',
    le_cylindrical text DEFAULT '',
    le_axis text DEFAULT '',
    le_diameter text DEFAULT '',
    le_movement text DEFAULT '',
    le_centralization text DEFAULT '',
    le_spin text DEFAULT '',
    le_fluorescein text DEFAULT '',
    le_over_refraction text DEFAULT '',
    le_bichrome text DEFAULT '',
    le_client_approved boolean DEFAULT false,
    le_client_purchased boolean DEFAULT false,
    le_delivered boolean DEFAULT false,

    re_item text DEFAULT '',
    re_brand text DEFAULT '',
    re_base_curve text DEFAULT '',
    re_spherical_degree text DEFAULT '',
    re_cylindrical text DEFAULT '',
    re_axis text DEFAULT '',
    re_diameter text DEFAULT '',
    re_movement text DEFAULT '',
    re_centralization text DEFAULT '',
    re_spin text DEFAULT '',
    re_fluorescein text DEFAULT '',
    re_over_refraction text DEFAULT '',
    re_bichrome text DEFAULT '',
    re_client_approved boolean DEFAULT false,
    re_client_purchased boolean DEFAULT false,
    re_delivered boolean DEFAULT false,

    notes text DEFAULT ''
);

CREATE TABLE optical_patient_visual_acuity (
    id uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id),
    create_date timestamp NOT NULL,
    client_id uuid NOT NULL REFERENCES client(id) ON UPDATE CASCADE,
    responsible_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,

    be_distance_glasses text DEFAULT '',
    le_distance_glasses text DEFAULT '',
    re_distance_glasses text DEFAULT '',

    be_distance_lenses text DEFAULT '',
    le_distance_lenses text DEFAULT '',
    re_distance_lenses text DEFAULT '',

    be_near_glasses text DEFAULT '',
    be_near_lenses text DEFAULT '',
    notes text DEFAULT ''
);
