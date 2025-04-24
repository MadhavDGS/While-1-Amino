-- Create the protein_searches table
create table protein_searches (
    id uuid default uuid_generate_v4() primary key,
    protein_id text,
    protein_name text,
    gene_names text[],
    organism text,
    timestamp timestamptz default now(),
    full_data jsonb,
    summary text
);

-- Create index for faster searches
create index protein_searches_timestamp_idx on protein_searches(timestamp desc);
create index protein_searches_protein_id_idx on protein_searches(protein_id);

-- Enable Row Level Security (RLS)
alter table protein_searches enable row level security;

-- Create policy to allow all operations (for demo purposes)
create policy "Enable all operations for all users" on protein_searches
    for all
    using (true)
    with check (true); 