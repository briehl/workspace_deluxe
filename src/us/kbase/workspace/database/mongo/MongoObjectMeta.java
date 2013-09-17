package us.kbase.workspace.database.mongo;

import java.util.Date;

import us.kbase.workspace.database.ObjectMetaData;
import us.kbase.workspace.database.WorkspaceUser;

public class MongoObjectMeta implements ObjectMetaData {
	
	final private int id;
	final private String name;
	final private String type;
	final private Date createdDate;
	final private int version;
	final private WorkspaceUser creator;
	final private int workspaceId;
	final private String chksum;
	final private int size;
	
	MongoObjectMeta(final int id, final String name,
			final String typeString, final Date createdDate, final int version,
			final WorkspaceUser creator, final ResolvedMongoWSID workspaceid,
			final String chksum,
			final int size) {
		//no error checking for now, add if needed
		this.id = id;
		this.name = name;
		this.type = typeString;
		this.createdDate = createdDate;
		this.version = version;
		this.creator = creator;
		this.workspaceId = workspaceid.getID();
		this.chksum = chksum;
		this.size = size;
		
	}

	@Override
	public int getObjectId() {
		return id;
	}

	@Override
	public String getObjectName() {
		return name;
	}

	@Override
	public String getTypeString() {
		return type;
	}

	@Override
	public Date getCreatedDate() {
		return createdDate;
	}

	@Override
	public int getVersion() {
		return version;
	}

	@Override
	public WorkspaceUser getCreator() {
		return creator;
	}

	@Override
	public int getWorkspaceId() {
		return workspaceId;
	}

	@Override
	public String getCheckSum() {
		return chksum;
	}
	
	
	@Override
	public int getSize() {
		return size;
	}

	@Override
	public String toString() {
		return "MongoObjectMeta [id=" + id + ", name=" + name + ", type="
				+ type + ", createdDate=" + createdDate + ", version="
				+ version + ", creator=" + creator + ", workspaceId="
				+ workspaceId + ", chksum=" + chksum + "]";
	}

}