from supabase import create_client
import json
from datetime import datetime

# Supabase configuration
SUPABASE_URL = "https://bpzpbrjoefkpagokkskm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwenBicmpvZWZrcGFnb2trc2ttIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1MTAwMDYsImV4cCI6MjA2MTA4NjAwNn0._u2BUcWadd7IFLxEgT_ALhhjQZXKfJwa-YnDDwTAB0U"

class SupabaseManager:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    def store_search(self, protein_data):
        """Store protein search data in Supabase"""
        try:
            basic_info = protein_data.get('basic_info', {})
            
            # Prepare the data for storage
            search_data = {
                'protein_id': basic_info.get('uniprot_id'),
                'protein_name': basic_info.get('protein_name'),
                'gene_names': basic_info.get('gene_names', []),
                'organism': basic_info.get('organism'),
                'timestamp': datetime.now().isoformat(),
                'full_data': json.dumps(protein_data),  # Store complete data as JSON
                'summary': basic_info.get('summary', '')[:500]  # Store first 500 chars of summary
            }
            
            # Insert into Supabase
            result = self.supabase.table('protein_searches').insert(search_data).execute()
            return result.data
            
        except Exception as e:
            print(f"Error storing search: {str(e)}")
            return None
    
    def get_search_history(self):
        """Retrieve search history from Supabase"""
        try:
            result = self.supabase.table('protein_searches')\
                .select('*')\
                .order('timestamp', desc=True)\
                .execute()
            return result.data
        except Exception as e:
            print(f"Error retrieving search history: {str(e)}")
            return []
    
    def get_protein_data(self, search_id):
        """Retrieve full protein data for a specific search"""
        try:
            result = self.supabase.table('protein_searches')\
                .select('full_data')\
                .eq('id', search_id)\
                .single()\
                .execute()
            return json.loads(result.data['full_data'])
        except Exception as e:
            print(f"Error retrieving protein data: {str(e)}")
            return None
    
    def delete_search(self, search_id):
        """Delete a specific search from history"""
        try:
            result = self.supabase.table('protein_searches')\
                .delete()\
                .eq('id', search_id)\
                .execute()
            return result.data
        except Exception as e:
            print(f"Error deleting search: {str(e)}")
            return None 