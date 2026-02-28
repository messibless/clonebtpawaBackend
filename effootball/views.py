from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from .models import Efootbal
from .serializers import EfootbalSerializer

# Create your views here.




class EfootballListCreateView(APIView):
    """
    View to list and create efootball
    """
    
    def get(self, request):
        """Get all match fixtures"""
        fixtures = Efootbal.objects.all().order_by('date', 'time')
        serializer = EfootbalSerializer(fixtures, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new match fixture"""
        print("📥 Received data:", request.data)  # Debug print
        
        serializer = EfootbalSerializer(data=request.data)
        
        if serializer.is_valid():
            fixture = serializer.save()
            print("✅ Created fixture:", fixture.id)
            return Response(
                EfootbalSerializer(fixture).data,
                status=status.HTTP_201_CREATED
            )
        
        print("❌ Serializer errors:", serializer.errors)  # Debug print
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EfootbalDetailView(APIView):
    """
    View to retrieve, update or delete a match fixture
    """
    
    def get_object(self, pk):
        try:
            return Efootbal.objects.get(pk=pk)
        except Efootbal.DoesNotExist:
            return None
    
    # ============================================
    # GET single fixture - /api/fixtures/<id>/
    # ============================================
    def get(self, request, pk):
        """Get a single match fixture by ID"""
        fixture = self.get_object(pk)
        
        if not fixture:
            return Response(
                {'error': 'Match fixture not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = EfootbalSerializer(fixture)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # ============================================
    # UPDATE full fixture - PUT /api/fixtures/<id>/
    # ============================================
    def put(self, request, pk):
        """Update entire match fixture"""
        fixture = self.get_object(pk)
        
        if not fixture:
            return Response(
                {'error': 'Match fixture not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        print(f"📥 Updating fixture {pk} with data:", request.data)
        
        serializer = EfootbalSerializer(fixture, data=request.data)
        
        if serializer.is_valid():
            updated_fixture = serializer.save()
            print(f"✅ Updated fixture {pk}")
            return Response(
                EfootbalSerializer(updated_fixture).data,
                status=status.HTTP_200_OK
            )
        
        print("❌ Update errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # ============================================
    # PARTIAL UPDATE - PATCH /api/fixtures/<id>/
    # ============================================
    def patch(self, request, pk):
        """Partially update a match fixture"""
        fixture = self.get_object(pk)
        
        if not fixture:
            return Response(
                {'error': 'Match fixture not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        print(f"📥 Partially updating fixture {pk} with data:", request.data)
        
        serializer = EfootbalSerializer(fixture, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_fixture = serializer.save()
            print(f"✅ Partially updated fixture {pk}")
            return Response(
                EfootbalSerializer(updated_fixture).data,
                status=status.HTTP_200_OK
            )
        
        print("❌ Partial update errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # ============================================
    # DELETE - DELETE /api/fixtures/<id>/
    # ============================================
    def delete(self, request, pk):
        """Delete a match fixture"""
        fixture = self.get_object(pk)
        
        if not fixture:
            return Response(
                {'error': 'Match fixture not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        fixture_info = {
            'id': fixture.id,
            'eventId': fixture.eventId,
            'message': f'Fixture {fixture.id} - {fixture.homeTeam} vs {fixture.awayTeam} deleted successfully'
        }
        
        fixture.delete()
        print(f"✅ Deleted fixture {pk}")
        
        return Response(fixture_info, status=status.HTTP_200_OK)


class EfootballBulkCreateView(APIView):
    """
    View to create multiple match fixtures at once
    """
    
    def post(self, request):
        """Create multiple match fixtures"""
        print("📥 Bulk create received:", len(request.data) if isinstance(request.data, list) else "Not a list")
        
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of fixtures'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_fixtures = []
        errors = []
        
        for index, fixture_data in enumerate(request.data):
            print(f"Processing fixture {index}:", fixture_data)
            serializer = EfootbalSerializer(data=fixture_data)
            if serializer.is_valid():
                fixture = serializer.save()
                created_fixtures.append(EfootbalSerializer(fixture).data)
                print(f"✅ Created fixture {index}")
            else:
                errors.append({
                    'index': index,
                    'data': fixture_data,
                    'errors': serializer.errors
                })
                print(f"❌ Error in fixture {index}:", serializer.errors)
        
        response_data = {
            'created': created_fixtures,
            'errors': errors,
            'total_created': len(created_fixtures),
            'total_errors': len(errors)
        }
        
        status_code = status.HTTP_201_CREATED if created_fixtures else status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=status_code)
   


class EfootballBulkUpdateView(APIView):
    """
    View to update multiple match fixtures at once
    """
    
    def put(self, request):
        """Update multiple match fixtures"""
        print("📥 Bulk update received:", len(request.data) if isinstance(request.data, list) else "Not a list")
        
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of fixtures with ids'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_fixtures = []
        errors = []
        
        for index, fixture_data in enumerate(request.data):
            fixture_id = fixture_data.get('id')
            
            if not fixture_id:
                errors.append({
                    'index': index,
                    'data': fixture_data,
                    'errors': {'id': 'This field is required for updates'}
                })
                continue
            
            try:
                fixture = Efootbal.objects.get(pk=fixture_id)
                serializer = EfootbalSerializer(fixture, data=fixture_data)
                
                if serializer.is_valid():
                    updated_fixture = serializer.save()
                    updated_fixtures.append(EfootbalSerializer(updated_fixture).data)
                    print(f"✅ Updated fixture {fixture_id}")
                else:
                    errors.append({
                        'index': index,
                        'id': fixture_id,
                        'data': fixture_data,
                        'errors': serializer.errors
                    })
                    print(f"❌ Error updating fixture {fixture_id}:", serializer.errors)
                    
            except Efootbal.DoesNotExist:
                errors.append({
                    'index': index,
                    'id': fixture_id,
                    'data': fixture_data,
                    'errors': {'id': f'Fixture with id {fixture_id} not found'}
                })
        
        response_data = {
            'updated': updated_fixtures,
            'errors': errors,
            'total_updated': len(updated_fixtures),
            'total_errors': len(errors)
        }
        
        status_code = status.HTTP_200_OK if updated_fixtures else status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=status_code)


class EfootballBulkDeleteView(APIView):
    """
    View to delete multiple match fixtures at once
    """
    
    def delete(self, request):
        """Delete multiple match fixtures"""
        fixture_ids = request.data.get('ids', [])
        
        if not fixture_ids:
            return Response(
                {'error': 'Expected a list of fixture ids'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted = []
        not_found = []
        
        for fixture_id in fixture_ids:
            try:
                fixture = Efootbal.objects.get(pk=fixture_id)
                fixture_info = {
                    'id': fixture.id,
                    'eventId': fixture.eventId,
                    'homeTeam': fixture.homeTeam,
                    'awayTeam': fixture.awayTeam
                }
                fixture.delete()
                deleted.append(fixture_info)
                print(f"✅ Deleted fixture {fixture_id}")
            except Efootbal.DoesNotExist:
                not_found.append(fixture_id)
                print(f"❌ Fixture {fixture_id} not found")
        
        response_data = {
            'deleted': deleted,
            'not_found': not_found,
            'total_deleted': len(deleted),
            'total_not_found': len(not_found)
        }
        
        status_code = status.HTTP_200_OK if deleted else status.HTTP_404_NOT_FOUND
        return Response(response_data, status=status_code)