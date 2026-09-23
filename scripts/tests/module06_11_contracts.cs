using CleanCodeDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var legacy=new LegacyCalculator();var policy=new LoyaltyPolicy();var random=new Random(12345);
 var values=new List<decimal>{-1,0,1,99999,100000,4999999,5000000,5000001,9999999,10000000,10000001};
 for(int i=0;i<1000;i++)values.Add(random.Next(0,20000000));
 foreach(var value in values)foreach(bool doubled in new[]{false,true}){
  var clean=policy.Evaluate(new CustomerSpending("a",value),doubled?PointsCampaign.DoublePoints:PointsCampaign.Standard);
  Check(legacy.Do(new Cust("a",value),doubled)==LoyaltyStatusFormatter.ToCompactCode(clean),"bounded characterization");
 }
 Check(policy.Evaluate(new CustomerSpending("a",5000000),PointsCampaign.Standard)==new LoyaltyStatus(LoyaltyTier.Gold,50),"independent boundary oracle");
 Check(legacy.Do(null,false)=="","legacy null contract");Throws<ArgumentNullException>(()=>policy.Evaluate(null!,PointsCampaign.Standard));

 }

}
