import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  FlatList,
  Alert,
} from 'react-native';
import { useSelector } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import apiClient from '../../config/api';
import TemplateItem from '../../components/TemplateItem';
import TemplateModal from '../../components/TemplateModal';

const TemplatesScreen = ({ navigation }) => {
  const { user } = useSelector((state) => state.auth);
  const { activeSprint } = useSelector((state) => state.sprint);

  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [selectedTemplates, setSelectedTemplates] = useState(new Set());
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [applyingTemplates, setApplyingTemplates] = useState(false);

  useEffect(() => {
    if (user?.id) {
      fetchData();
    }
  }, [user]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [templatesRes, categoriesRes] = await Promise.all([
        apiClient.get(`/templates/${user.id}`),
        apiClient.get(`/categories/${user.id}`),
      ]);
      setTemplates(templatesRes.data);
      setCategories(categoriesRes.data);
      setSelectedTemplates(new Set());
    } catch (error) {
      console.error('Error fetching templates:', error);
      Alert.alert('Error', 'No se pudieron cargar las plantillas');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = async (data) => {
    try {
      const response = await apiClient.post(
        `/templates?user_id=${user.id}`,
        data
      );
      setTemplates([...templates, response.data]);
      setModalVisible(false);
    } catch (error) {
      console.error('Error creating template:', error);
      throw error;
    }
  };

  const handleUpdateTemplate = async (data) => {
    try {
      const response = await apiClient.patch(
        `/templates/${editingTemplate.id}`,
        data
      );
      setTemplates(
        templates.map((t) => (t.id === editingTemplate.id ? response.data : t))
      );
      setModalVisible(false);
      setEditingTemplate(null);
    } catch (error) {
      console.error('Error updating template:', error);
      throw error;
    }
  };

  const handleDeleteTemplate = (templateId, templateName) => {
    Alert.alert(
      'Eliminar Plantilla',
      `¿Estás seguro de que quieres eliminar "${templateName}"?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Eliminar',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiClient.delete(
                `/templates/${templateId}?user_id=${user.id}`
              );
              setTemplates(templates.filter((t) => t.id !== templateId));
            } catch (error) {
              console.error('Error deleting template:', error);
              Alert.alert('Error', 'No se pudo eliminar la plantilla');
            }
          },
        },
      ]
    );
  };

  const handleSelectTemplate = (template) => {
    if (!isSelectionMode) {
      setIsSelectionMode(true);
    }
    const newSelected = new Set(selectedTemplates);
    if (newSelected.has(template.id)) {
      newSelected.delete(template.id);
    } else {
      newSelected.add(template.id);
    }
    if (newSelected.size === 0) {
      setIsSelectionMode(false);
    }
    setSelectedTemplates(newSelected);
  };

  const handleApplyTemplates = async () => {
    if (selectedTemplates.size === 0) {
      Alert.alert('Error', 'Selecciona al menos una plantilla');
      return;
    }

    if (!activeSprint?.id) {
      Alert.alert('Error', 'No hay sprint activo');
      return;
    }

    try {
      setApplyingTemplates(true);
      const templateIds = Array.from(selectedTemplates);
      const accountId = null;

      await apiClient.post(
        `/templates/${activeSprint.id}/apply-templates?user_id=${user.id}`,
        {
          template_ids: templateIds,
          account_id: accountId,
        }
      );

      Alert.alert(
        'Éxito',
        `Se aplicaron ${selectedTemplates.size} plantilla(s) al sprint`
      );
      setSelectedTemplates(new Set());
      setIsSelectionMode(false);
      navigation.goBack();
    } catch (error) {
      console.error('Error applying templates:', error);
      Alert.alert('Error', 'No se pudieron aplicar las plantillas');
    } finally {
      setApplyingTemplates(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Plantillas de Gastos</Text>
          <Text style={styles.subtitle}>
            Gastos fijos reutilizables
          </Text>
        </View>
        {!isSelectionMode && (
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => {
              setEditingTemplate(null);
              setModalVisible(true);
            }}
          >
            <Ionicons name="add" size={28} color="#fff" />
          </TouchableOpacity>
        )}
      </View>

      <FlatList
        data={templates}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <TemplateItem
            template={item}
            isSelected={selectedTemplates.has(item.id)}
            onSelect={isSelectionMode ? handleSelectTemplate : undefined}
            onEdit={() => {
              setEditingTemplate(item);
              setModalVisible(true);
            }}
            onDelete={() => handleDeleteTemplate(item.id, item.name)}
          />
        )}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyCard}>
            <Ionicons
              name="bookmark-outline"
              size={48}
              color="#ddd"
              style={{ marginBottom: 12 }}
            />
            <Text style={styles.emptyText}>No hay plantillas</Text>
            <Text style={styles.emptySubtext}>
              Crea plantillas para reutilizar tus gastos fijos
            </Text>
          </View>
        }
      />

      {isSelectionMode && activeSprint && (
        <View style={styles.actionBar}>
          <TouchableOpacity
            style={styles.cancelButton}
            onPress={() => {
              setSelectedTemplates(new Set());
              setIsSelectionMode(false);
            }}
          >
            <Text style={styles.cancelButtonText}>
              Cancelar ({selectedTemplates.size})
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.applyButton,
              applyingTemplates && styles.applyButtonDisabled,
            ]}
            onPress={handleApplyTemplates}
            disabled={applyingTemplates}
          >
            {applyingTemplates ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.applyButtonText}>Aplicar</Text>
            )}
          </TouchableOpacity>
        </View>
      )}

      <TemplateModal
        visible={modalVisible}
        onClose={() => {
          setModalVisible(false);
          setEditingTemplate(null);
        }}
        onSubmit={editingTemplate ? handleUpdateTemplate : handleCreateTemplate}
        editingTemplate={editingTemplate}
        categories={categories}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 12,
    color: '#999',
  },
  addButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: 16,
  },
  emptyCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    marginTop: 20,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#999',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#bbb',
  },
  actionBar: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f0f0f0',
  },
  cancelButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '600',
  },
  applyButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
  },
  applyButtonDisabled: {
    opacity: 0.6,
  },
  applyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default TemplatesScreen;
