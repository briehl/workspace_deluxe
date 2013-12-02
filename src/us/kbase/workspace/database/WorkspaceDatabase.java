package us.kbase.workspace.database;

import java.util.List;
import java.util.Map;
import java.util.Set;

import us.kbase.typedobj.core.TypeDefId;
import us.kbase.typedobj.core.TypedObjectValidator;
import us.kbase.workspace.database.exceptions.CorruptWorkspaceDBException;
import us.kbase.workspace.database.exceptions.NoSuchObjectException;
import us.kbase.workspace.database.exceptions.NoSuchWorkspaceException;
import us.kbase.workspace.database.exceptions.PreExistingWorkspaceException;
import us.kbase.workspace.database.exceptions.WorkspaceCommunicationException;
import us.kbase.workspace.workspaces.ResolvedSaveObject;

public interface WorkspaceDatabase {
	
	public String getBackendType();
	
	public TypedObjectValidator getTypeValidator();
	
	public ResolvedWorkspaceID resolveWorkspace(final WorkspaceIdentifier wsi)
			throws NoSuchWorkspaceException, WorkspaceCommunicationException;
	
	public Map<WorkspaceIdentifier, ResolvedWorkspaceID> resolveWorkspaces(
			Set<WorkspaceIdentifier> rwsis) throws NoSuchWorkspaceException,
			WorkspaceCommunicationException;

	public ResolvedWorkspaceID resolveWorkspace(WorkspaceIdentifier wsi,
			boolean allowDeleted) throws NoSuchWorkspaceException,
			WorkspaceCommunicationException;
	
	public Map<WorkspaceIdentifier, ResolvedWorkspaceID> resolveWorkspaces(
			Set<WorkspaceIdentifier> wsis, boolean allowDeleted)
			throws NoSuchWorkspaceException, WorkspaceCommunicationException;

	public WorkspaceInformation createWorkspace(WorkspaceUser owner, String wsname,
			boolean globalread, String description) throws
			PreExistingWorkspaceException, WorkspaceCommunicationException,
			CorruptWorkspaceDBException;
	
	public void setPermissions(ResolvedWorkspaceID rwsi,
			List<WorkspaceUser> users, Permission perm) throws
			WorkspaceCommunicationException, CorruptWorkspaceDBException;
	
	public void setGlobalPermission(ResolvedWorkspaceID rwsi, Permission perm)
			throws 	WorkspaceCommunicationException, CorruptWorkspaceDBException;
	
	public Permission getPermission(WorkspaceUser user,
			ResolvedWorkspaceID rwsi)
			throws WorkspaceCommunicationException, CorruptWorkspaceDBException;
	
	public PermissionSet getPermissions(WorkspaceUser user,
			ResolvedWorkspaceID rwsi) throws 
			WorkspaceCommunicationException, CorruptWorkspaceDBException;
	
	public PermissionSet getPermissions(WorkspaceUser user,
			Set<ResolvedWorkspaceID> rwsis)
			throws WorkspaceCommunicationException, CorruptWorkspaceDBException;

	public Map<User, Permission> getAllPermissions(
			ResolvedWorkspaceID rwsi) throws WorkspaceCommunicationException,
			CorruptWorkspaceDBException;

	public WorkspaceInformation getWorkspaceInformation(WorkspaceUser user,
			ResolvedWorkspaceID rwsi) throws CorruptWorkspaceDBException,
			WorkspaceCommunicationException;
	
	public void setWorkspaceDescription(ResolvedWorkspaceID wsid,
			String description) throws WorkspaceCommunicationException;

	public String getWorkspaceDescription(ResolvedWorkspaceID rwsi)
			throws WorkspaceCommunicationException, CorruptWorkspaceDBException;
	
	public List<ObjectInformation> saveObjects(WorkspaceUser user,
			ResolvedWorkspaceID rwsi, List<ResolvedSaveObject> objects) throws
			NoSuchWorkspaceException, WorkspaceCommunicationException,
			NoSuchObjectException;
	
	public Map<ObjectIDResolvedWS, WorkspaceObjectData> getObjects(
			Set<ObjectIDResolvedWS> objectIDs) throws NoSuchObjectException,
			WorkspaceCommunicationException, CorruptWorkspaceDBException;

	public Map<ObjectIDResolvedWS, ObjectInformation> getObjectInformation(
			Set<ObjectIDResolvedWS> objectIDs, boolean includeMetadata)
			throws NoSuchObjectException, WorkspaceCommunicationException;
	
	public Map<ObjectIDResolvedWS, TypeAndReference> getObjectType(
			final Set<ObjectIDResolvedWS> objectIDs) throws
			NoSuchObjectException, WorkspaceCommunicationException;

	public ObjectInformation copyObject(WorkspaceUser user, 
			ObjectIDResolvedWS from, ObjectIDResolvedWS to)
			throws NoSuchObjectException, WorkspaceCommunicationException;
	
	public ObjectInformation revertObject(WorkspaceUser user,
			ObjectIDResolvedWS target)
			throws NoSuchObjectException, WorkspaceCommunicationException;
	
	public WorkspaceInformation renameWorkspace(WorkspaceUser user,
			ResolvedWorkspaceID wsid, String newname)
			throws WorkspaceCommunicationException, CorruptWorkspaceDBException;
	
	public ObjectInformation renameObject(
			ObjectIDResolvedWS object, String newname)
			throws NoSuchObjectException, WorkspaceCommunicationException;
	
	public void setObjectsHidden(Set<ObjectIDResolvedWS> objectIDs,
			boolean hide) throws NoSuchObjectException,
			WorkspaceCommunicationException;
	
	public void setObjectsDeleted(Set<ObjectIDResolvedWS> objectIDs,
			boolean delete) throws NoSuchObjectException,
			WorkspaceCommunicationException;

	public void setWorkspaceDeleted(ResolvedWorkspaceID wsid, boolean delete)
			throws WorkspaceCommunicationException;

	public PermissionSet getWorkspacesWithPermission(WorkspaceUser user,
			Permission perm) throws WorkspaceCommunicationException,
			CorruptWorkspaceDBException;

	public List<WorkspaceInformation> getWorkspaceInformation(
			PermissionSet pset, boolean excludeGlobal, boolean showDeleted)
			throws WorkspaceCommunicationException, CorruptWorkspaceDBException;

	public List<ObjectInformation> getObjectInformation(
			PermissionSet pset, TypeDefId type, boolean showHidden,
			boolean showDeleted, boolean showAllVers, boolean includeMetaData)
			throws WorkspaceCommunicationException;

	public List<ObjectInformation> getObjectHistory(
			ObjectIDResolvedWS objectIDResolvedWS)
			throws NoSuchObjectException, WorkspaceCommunicationException;
}
