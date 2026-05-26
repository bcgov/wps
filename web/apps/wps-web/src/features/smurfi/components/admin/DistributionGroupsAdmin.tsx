import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import {
  DistributionGroup,
  DistributionGroupInput,
  deleteDistributionGroup,
  getDistributionGroups,
  postDistributionGroup,
  putDistributionGroup
} from '@wps/api/SMURFIAPI'
import { useEffect, useState } from 'react'

const EMPTY_FORM: DistributionGroupInput = { name: '', emails: [] }

const DistributionGroupsAdmin = () => {
  const { isForecaster } = useSpotPermissions(undefined)

  const [groups, setGroups] = useState<DistributionGroup[]>([])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<DistributionGroup | null>(null)
  const [formValues, setFormValues] = useState<DistributionGroupInput>(EMPTY_FORM)
  const [emailInput, setEmailInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadGroups = () => getDistributionGroups().then(setGroups).catch(() => setGroups([]))

  useEffect(() => {
    loadGroups()
  }, [])

  const openCreate = () => {
    setEditingGroup(null)
    setFormValues(EMPTY_FORM)
    setEmailInput('')
    setError(null)
    setDialogOpen(true)
  }

  const openEdit = (group: DistributionGroup) => {
    setEditingGroup(group)
    setFormValues({ name: group.name, emails: [...group.emails] })
    setEmailInput('')
    setError(null)
    setDialogOpen(true)
  }

  const handleClose = () => {
    setDialogOpen(false)
  }

  const commitEmailInput = () => {
    const trimmed = emailInput.trim()
    if (trimmed && !formValues.emails.includes(trimmed)) {
      setFormValues(v => ({ ...v, emails: [...v.emails, trimmed] }))
    }
    setEmailInput('')
  }

  const removeEmail = (email: string) => {
    setFormValues(v => ({ ...v, emails: v.emails.filter(e => e !== email) }))
  }

  const handleCsvUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = e => {
      const text = e.target?.result as string
      const emailRegex = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g
      const found = text.match(emailRegex) ?? []
      setFormValues(v => {
        const existing = new Set(v.emails)
        const added = found.filter(email => !existing.has(email.toLowerCase())).map(e => e.toLowerCase())
        return { ...v, emails: [...v.emails, ...added] }
      })
    }
    reader.readAsText(file)
    event.target.value = ''
  }

  const handleSave = async () => {
    commitEmailInput()
    const payload = { ...formValues }
    if (emailInput.trim() && !payload.emails.includes(emailInput.trim())) {
      payload.emails = [...payload.emails, emailInput.trim()]
    }
    if (!payload.name.trim()) {
      setError('Name is required')
      return
    }
    setSaving(true)
    setError(null)
    try {
      if (editingGroup) {
        await putDistributionGroup(editingGroup.id, payload)
      } else {
        await postDistributionGroup(payload)
      }
      await loadGroups()
      setDialogOpen(false)
    } catch {
      setError('Failed to save distribution group')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (group: DistributionGroup) => {
    if (!window.confirm(`Delete "${group.name}"?`)) return
    try {
      await deleteDistributionGroup(group.id)
      await loadGroups()
    } catch {
      // ignore
    }
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Stack direction="row" sx={{ mb: 2, alignItems: 'center' }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>Distribution Groups</Typography>
        {isForecaster && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
            New Group
          </Button>
        )}
      </Stack>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Members</TableCell>
              <TableCell>Created by</TableCell>
              <TableCell>Last edited by</TableCell>
              <TableCell align="right" />
            </TableRow>
          </TableHead>
          <TableBody>
            {groups.length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>
                  <Typography variant="body2" color="text.secondary">
                    No distribution groups yet.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {groups.map(group => (
              <TableRow key={group.id}>
                <TableCell>{group.name}</TableCell>
                <TableCell>{group.emails.length}</TableCell>
                <TableCell>{group.created_by}</TableCell>
                <TableCell>{group.updated_by ?? '—'}</TableCell>
                <TableCell align="right">
                  {isForecaster && (
                    <>
                      <IconButton size="small" onClick={() => openEdit(group)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDelete(group)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>{editingGroup ? 'Edit Distribution Group' : 'New Distribution Group'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Group Name"
              value={formValues.name}
              onChange={e => setFormValues(v => ({ ...v, name: e.target.value }))}
              fullWidth
              size="small"
              error={!!error && !formValues.name.trim()}
            />
            <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start' }}>
              <TextField
                label="Add Email"
                value={emailInput}
                onChange={e => setEmailInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    commitEmailInput()
                  }
                }}
                onBlur={commitEmailInput}
                fullWidth
                size="small"
                helperText="Press Enter or Space to add"
              />
              <Box>
                <input
                  id="csv-upload"
                  type="file"
                  accept=".csv,text/csv"
                  style={{ display: 'none' }}
                  onChange={handleCsvUpload}
                />
                <label htmlFor="csv-upload">
                  <Button
                    component="span"
                    variant="outlined"
                    size="small"
                    startIcon={<UploadFileIcon />}
                    sx={{ mt: 0.25, whiteSpace: 'nowrap' }}
                  >
                    Import CSV
                  </Button>
                </label>
              </Box>
            </Stack>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {formValues.emails.map(email => (
                <Chip key={email} label={email} size="small" onDelete={() => removeEmail(email)} />
              ))}
            </Box>
            {error && (
              <Typography variant="caption" color="error">
                {error}
              </Typography>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default DistributionGroupsAdmin
