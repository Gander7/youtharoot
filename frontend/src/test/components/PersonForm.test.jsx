import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import PersonForm from '../../components/PersonForm.jsx';

vi.mock('../../stores/auth', () => ({
  apiRequest: vi.fn(),
}));

vi.mock('@mui/material/styles', () => ({
  ThemeProvider: ({ children }) => children,
  createTheme: () => ({}),
}));

const baseYouth = {
  id: 1,
  first_name: 'Alex',
  last_name: 'Smith',
  birth_date: '2010-06-15',
  person_type: 'youth',
  parental_permission_2026: false,
  photo_consent_2026: false,
};

describe('PersonForm - Youth consent checkboxes', () => {
  it('renders Parental Permission checkbox on Personal Info tab', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Parental Permission')).toBeInTheDocument();
  });

  it('renders Photo Consent checkbox on Personal Info tab', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Photo Consent')).toBeInTheDocument();
  });

  it('defaults both checkboxes to unchecked when creating a new youth', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Parental Permission')).not.toBeChecked();
    expect(screen.getByLabelText('Photo Consent')).not.toBeChecked();
  });

  it('reflects true values from existing youth record', () => {
    const youth = { ...baseYouth, parental_permission_2026: true, photo_consent_2026: true };
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={youth}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Parental Permission')).toBeChecked();
    expect(screen.getByLabelText('Photo Consent')).toBeChecked();
  });

  it('reflects mixed values from existing youth record', () => {
    const youth = { ...baseYouth, parental_permission_2026: true, photo_consent_2026: false };
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={youth}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Parental Permission')).toBeChecked();
    expect(screen.getByLabelText('Photo Consent')).not.toBeChecked();
  });

  it('defaults null consent values to unchecked (defensive — old records)', () => {
    const youth = { ...baseYouth, parental_permission_2026: null, photo_consent_2026: null };
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={youth}
        onSave={() => {}}
        personType="youth"
      />
    );
    expect(screen.getByLabelText('Parental Permission')).not.toBeChecked();
    expect(screen.getByLabelText('Photo Consent')).not.toBeChecked();
  });

  it('does not render consent checkboxes for leader form', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="leader"
      />
    );
    expect(screen.queryByLabelText('Parental Permission')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Photo Consent')).not.toBeInTheDocument();
  });

  it('does not render consent checkboxes for parent form', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="parent"
      />
    );
    expect(screen.queryByLabelText('Parental Permission')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Photo Consent')).not.toBeInTheDocument();
  });

  it('checkbox is interactive — toggling updates state', () => {
    render(
      <PersonForm
        open={true}
        onClose={() => {}}
        person={null}
        onSave={() => {}}
        personType="youth"
      />
    );
    const checkbox = screen.getByLabelText('Parental Permission');
    expect(checkbox).not.toBeChecked();
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
    fireEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });
});
