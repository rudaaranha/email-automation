import pytest


class TestGoogleSheets:
    """Integration tests with Google Sheets"""

    @pytest.mark.integration
    def test_google_client_conection(self, google_client):
        """ Conection test with Google Sheets"""
        assert google_client is not None
        print('success in establishing a connection')
    
    @pytest.mark.integration
    def test_open_first_spreadsheet(self, google_client, config):
        """Open first spreadsheet test"""
        first_project = list(config.SPREADSHEETS.keys())[0]
        spreasheet_id = config.SPREADSHEETS[first_project]

        spreadsheet = google_client.open_by_key(spreasheet_id)
        assert spreadsheet is not None
        print(f'Planilha: {spreadsheet.title}')

    @pytest.mark.integration
    def test_spreadsheet_data_read(self, google_client, config):
        first_project = list(config.SPREADSHEETS.keys())[0]
        spreadsheet_id = config.SPREADSHEETS[first_project]

        spreadsheet = google_client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(config.ACTIVITIES_WORKSHEET)
        data = worksheet.get_all_values()

        assert len(data) > 0, "Worksheet is empty"
        print(f'{len(data)} read lines')
        print(f'Header: {data[0][:3]}...')


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s', '-m integration'])
