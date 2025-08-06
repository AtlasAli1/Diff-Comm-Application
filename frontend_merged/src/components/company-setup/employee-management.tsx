'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Search, MoreHorizontal, Edit, Trash2, Plus, Upload, UserPlus } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { employeeService } from '@/lib/api/services'
import { useAppState } from '@/contexts/AppStateContext'
import { formatCurrency, getEmployeeStatusColor, formatPayType } from '@/lib/utils'
import { toast } from 'sonner'

export function EmployeeManagement() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const { setLoading } = useAppState()
  const queryClient = useQueryClient()

  // Get real employees from our API
  const { data: employeesResponse, isLoading } = useQuery({
    queryKey: ['employees', statusFilter, searchTerm],
    queryFn: () => employeeService.getEmployees({
      status: statusFilter === 'all' ? undefined : statusFilter,
      search: searchTerm || undefined,
    }),
  });

  // Delete employee mutation
  const deleteMutation = useMutation({
    mutationFn: employeeService.deleteEmployee,
    onMutate: () => setLoading('employees', true),
    onSuccess: () => {
      toast.success('Employee deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
    onError: (error) => {
      toast.error('Failed to delete employee');
      console.error('Delete error:', error);
    },
    onSettled: () => setLoading('employees', false),
  });

  const handleDelete = (id: number, name: string) => {
    if (confirm(`Are you sure you want to delete ${name}? This action cannot be undone.`)) {
      deleteMutation.mutate(id);
    }
  };

  // Get initials for avatar
  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName[0]}${lastName[0]}`.toUpperCase();
  };

  const employees = employeesResponse?.items || [];
  
  const filteredEmployees = employees.filter(employee => {
    const matchesSearch = searchTerm === '' || 
      employee.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      employee.status.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || employee.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Employee Management</CardTitle>
          <CardDescription>Loading employee data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Employee Management</CardTitle>
            <CardDescription>
              Manage employee information, statuses, and commission configuration
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Upload className="h-4 w-4 mr-2" />
              Import CSV
            </Button>
            <Button variant="outline" size="sm">
              <UserPlus className="h-4 w-4 mr-2" />
              Smart Add
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Employee
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Filters - Our Business Logic */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search employees..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
          
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="Active">Active</SelectItem>
              <SelectItem value="Inactive">Inactive</SelectItem>
              <SelectItem value="Helper/Apprentice">Helper/Apprentice</SelectItem>
              <SelectItem value="Excluded from Payroll">Excluded from Payroll</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Employee Table - Our Real Data */}
        {employees.length === 0 ? (
          <div className="text-center py-12">
            <UserPlus className="h-8 w-8 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No employees found</h3>
            <p className="text-muted-foreground mb-4">
              Get started by adding your first employee or importing from CSV
            </p>
            <div className="flex gap-2 justify-center">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Employee
              </Button>
              <Button variant="outline">
                <Upload className="h-4 w-4 mr-2" />
                Import CSV
              </Button>
            </div>
          </div>
        ) : (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Pay Type</TableHead>
                  <TableHead>Hourly Rate</TableHead>
                  <TableHead>Commission Eligible</TableHead>
                  <TableHead className="w-[70px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEmployees.map((employee) => {
                  const isCommissionEligible = employee.status === 'Active' && 
                    !employee.status.includes('Helper') && 
                    !employee.status.includes('Excluded');
                  
                  return (
                    <TableRow key={employee.id}>
                      <TableCell>
                        <div className="flex items-center space-x-3">
                          <Avatar className="h-9 w-9">
                            <AvatarImage src={`/placeholder.svg`} alt={employee.full_name} />
                            <AvatarFallback className="text-sm">
                              {getInitials(employee.first_name, employee.last_name)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">{employee.full_name}</div>
                            <div className="text-sm text-muted-foreground">
                              ID: {employee.id}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <Badge variant={getEmployeeStatusColor(employee.status) as any}>
                          {employee.status}
                        </Badge>
                      </TableCell>
                      
                      <TableCell>
                        <div className="font-medium">
                          {employee.pay_type}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {employee.pay_type === 'Efficiency Pay' ? 'Max of hourly/commission' : 'Hourly + all commission'}
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <span className="font-medium">{formatCurrency(employee.hourly_rate)}</span>
                        <span className="text-muted-foreground text-sm">/hour</span>
                      </TableCell>
                      
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {isCommissionEligible ? (
                            <Badge variant="default" className="text-xs">
                              Eligible
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="text-xs">
                              Not Eligible
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit Employee
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Edit className="mr-2 h-4 w-4" />
                              Commission Overrides
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              className="text-destructive"
                              onClick={() => handleDelete(employee.id, employee.full_name)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Summary Stats */}
        {employees.length > 0 && (
          <div className="mt-6 flex items-center justify-between text-sm text-muted-foreground">
            <div>
              Showing {filteredEmployees.length} of {employees.length} employees
            </div>
            <div className="flex gap-4">
              <span>Active: {employees.filter(e => e.status === 'Active').length}</span>
              <span>Helpers: {employees.filter(e => e.status === 'Helper/Apprentice').length}</span>
              <span>Efficiency Pay: {employees.filter(e => e.pay_type === 'Efficiency Pay').length}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}