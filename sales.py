import pandas as pd
import numpy as np
import datetime

df_s = pd.read_csv('onlineRetail.csv', encoding = "ISO-8859-1" )
print(df_s.describe())
print(df_s.CustomerID.isnull().sum())


df_s = df_s[pd.notnull(df_s['CustomerID'])]
print(df_s.describe())
print(df_s.CustomerID.isnull().sum())

df_s = df_s[(df_s.InvoiceDate >= '2010-12-09') &
            (df_s.Country == "United Kingdom")]
print(df_s.describe())
print((df_s.CustomerID.isnull().sum()))

print(df_s.InvoiceNo.nunique())
print(df_s.CustomerID.nunique())

# Identify returns
df_s['returns'] = np.where(df_s['InvoiceNo'].str.contains('C'),1,0)
df_s['purchaseInvoice'] = np.where(df_s['InvoiceNo'].str.contains('C'),0,1)

#################################
# Create customer-level dataset #
#################################

columns = ['Customers']

cus = df_s.CustomerID.unique()
cus = cus.astype(int)
print(type(cus[0]))
df_cus = pd.DataFrame(data = cus,  columns = columns)

###########
# Recency #
###########

lastdate = datetime.datetime.strptime('10122011', '%d%m%Y').date()
df_s.InvoiceDate = pd.to_datetime(df_s.InvoiceDate)
print(type(df_s.iloc[10]['InvoiceDate']))

# Obtain # of days since most recent purchase
df_s['recency'] = (lastdate - df_s.InvoiceDate)
df_s['recency'] = df_s['recency'].dt.days

# remove returns so only consider the data of most recent *purchase*
df_rec = df_s[(df_s.returns == 0)]

# Obtain # of days since most recent purchase

df_r = df_rec.groupby('CustomerID').recency.agg({'recency':np.min})
print(df_r)


##df_r = df_rec.groupby('CustomerID')['CustomerID','recency'].agg({'CustomerID':[np.max],'recency':[np.min]})
##
##print(df_r)
# Add recency to customer data
merged_df = pd.merge (left = df_cus, right = df_r, left_on = "Customers",
                      right_index = True)
merged_df.sort_values(by=['Customers'])


#############
# Frequency #
#############

customer_invoice = df_s[['CustomerID','InvoiceNo','purchaseInvoice']]
customer_invoice.drop_duplicates()

# Number of invoices/year (purchases only)
annualInvoice = customer_invoice.groupby('CustomerID').purchaseInvoice.agg({'frequency':np.sum})

# Add # of invoices to customers data
merged_df = pd.merge(left = merged_df, right = annualInvoice, left_on="Customers",
                     right_index=True)

# Remove customers who have not made any purchases in the past year
customers_df = merged_df[merged_df.frequency>0]



###############################
# Monetary Value of Customers #
###############################

# Total spent on each item on an invoice
df_s['Amount'] = df_s.Quantity * df_s.UnitPrice

# Aggregated total sales to customer
annualSales = df_s.groupby('CustomerID').Amount.agg({'monetary':np.sum})

# Add monetary value to customers dataset
customers_df = pd.merge(left = customers_df, right = annualSales, left_on = 'Customers', right_index = True)

# Identify customers with negative monetary value numbers,
#as they were presumably returning purchases from the preceding year
customers_df.loc[(customers_df['monetary'] < 0) ] = 0


####################
# Pareto Principle #
####################

# Apply Pareto Principle (80/20 Rule)
pareto_cutoff = 0.8 * sum(customers_df.monetary)

customers_df = customers_df.sort_values(by=['monetary'], ascending = False)

customers_df['top20?'] = np.where(customers_df.monetary.cumsum() < pareto_cutoff,1,0)
